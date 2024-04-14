import boto3
from time import sleep

from asgebsmanager.mds_utils import get_imds_token, get_instance_metadata


class AsgEbsManager:

    def __init__(self,region,asg_name):
        self.asg_name = asg_name
        self.session = boto3.Session(region_name=region)
        self.ec2_client = self.session.client('ec2')

    @staticmethod
    def __get_name():
        return 'AsgEbsManager'
    
    def latest_volume(self,az=None,state=None):
        status = ["available","in-use"] if state is None else [state]
        filters = [
                {
                    'Name': 'tag:BelongsTo',
                    'Values': [
                        self.asg_name,
                    ]
                },
                {
                    'Name': 'tag:ManagedBy',
                    'Values': [
                        self.__get_name(),
                    ]
                },
                {
                    'Name': 'status',
                    'Values': status
                }
            ]
        if az is not None:
            filters.append({
                    'Name': 'availability-zone',
                    'Values': [
                        az,
                    ]
            })
        volumes = self.ec2_client.describe_volumes(
            Filters=filters,
            MaxResults=100
        )

        if len(volumes['Volumes']) > 0:
            sorted_volume = [volume['VolumeId'] for volume in sorted(volumes['Volumes'], key=lambda volume: volume['CreateTime'])]
            return sorted_volume[0]
        return None

    def create_volume(self,az,size,iops,throughput,snapshot_id=''):
        response = self.ec2_client.create_volume(
            SnapshotId=snapshot_id,
            AvailabilityZone=az,
            Encrypted=True,
            Iops=iops,
            Size=size,
            VolumeType='gp3',
            Throughput=throughput,
        )
        return response['VolumeId']
    
    def describe_volume(self,volume_id):
        volumes = self.ec2_client.describe_volumes(VolumeIds=[volume_id])['Volumes']
        volume = None
        if len(volumes) > 0:
            volume = volumes[0]
        if volume is None: 
            return None 
        return volume
    


    def attach_volume(self,volume_id,instance_id,device):
        response = self.ec2_client.attach_volume(
            Device=device,
            InstanceId=instance_id,
            VolumeId=volume_id
        )
        return response['VolumeId']
    
    def delete_volume(self,volume_id):
        self.ec2_client.delete_volume(
            VolumeId=volume_id
        )

    def create_snapshot(self,volume_id):
        response = self.ec2_client.create_snapshot(
            Description=f'SnapshotOf{volume_id}',
            VolumeId=volume_id
        )
        return response['SnapshotId']

    
    def delete_snapshot(self,snapshot_id):
        self.ec2_client.delete_snapshot(
            SnapshotId=snapshot_id
        )


    def describe_snapshot(self,snapshot_id):
        snapshots = self.ec2_client.describe_snapshots(SnapshotIds=[snapshot_id])['Snapshots']
        snapshot = None
        if len(snapshots) > 0:
            snapshot = snapshots[0]
        if snapshot is None: 
            return None 
        return snapshot
    
    def tag_resource(self,resource_id):
        self.ec2_client.create_tags(
            Resources=[
                resource_id,
            ],
            Tags=[
                {
                    'Key': 'BelongsTo',
                    'Value': self.asg_name,
                },
                {
                    'Key': 'ManagedBy',
                    'Value': self.__get_name(),
                }
            ]
        )

def manage_ebs(args):
    try: 
        asg_ebs_manager = AsgEbsManager(region=args.region,asg_name=args.asg_name)

        # get the current instance az and id
        mds_token = get_imds_token()

        az =  get_instance_metadata(mds_token,"placement/availability-zone")
        instance_id =  get_instance_metadata(mds_token,"instance-id")

        volume_id = asg_ebs_manager.latest_volume(az)
        # if volume_id is not None, there is chance we can get the available volume
        if volume_id is not None:
            # find the available volume
            volume_id = asg_ebs_manager.latest_volume(az,'available')
            # wait for some other volume to be available
            max_retries = args.check_timeout
            while volume_id is None and max_retries > 0:
                    sleep(60)
                    volume_id = asg_ebs_manager.latest_volume(az,'available')
                    max_retries -= 1
            if max_retries == 0:
                volume_id = None

        az_diff = False

        # try to find an available volume in other azs and create snapshot 
        if volume_id is None:
            volume_id = asg_ebs_manager.latest_volume()
            # if volume_id is not None, there is chance we can get the available volume
            if volume_id is not None:
                # find the available volume
                volume_id = asg_ebs_manager.latest_volume(state='available')
                # wait for some other volume to be available
                max_retries = args.check_timeout
                while volume_id is None and max_retries > 0:
                        sleep(60)
                        volume_id = asg_ebs_manager.latest_volume(state='available')
                        max_retries -= 1
                if max_retries == 0:
                    volume_id = None
                if volume_id is not None:
                    az_diff = True

        # only if 'force' is enabled
        # check the difference in the volume configuration and if there is a diff, 
        # create a new volume from the snapshot of the existing volume and
        # delete the older volume 
        if volume_id and args.force:
            volume = asg_ebs_manager.describe_volume(volume_id)
            snapshot_id = None
            if volume['Size'] != args.size or volume['Iops'] != args.iops or volume['Throughput'] != args.throughput or az_diff:
                snapshot_id = asg_ebs_manager.create_snapshot(volume_id)
                snapshot = asg_ebs_manager.describe_snapshot(snapshot_id)
                max_retries = args.check_timeout
                while snapshot['State'] != 'completed' and max_retries > 0:
                    sleep(60)
                    max_retries -= 1
                    snapshot = asg_ebs_manager.describe_snapshot(snapshot_id)
                # if snapshot is not getting created, attach the same volume
                if max_retries == 0:
                    snapshot_id = None

            # if the snapshot is created, create a new volume
            if snapshot_id:
                old_volume_id = volume_id
                asg_ebs_manager.tag_resource(snapshot_id)
                volume_id = asg_ebs_manager.create_volume(az,args.size,args.iops,args.throughput,snapshot_id=snapshot_id)
                max_retries = args.check_timeout
                volume = asg_ebs_manager.describe_volume(volume_id)
                while volume['State'] != 'available' and max_retries > 0:
                    sleep(60)
                    max_retries -= 1
                    volume = asg_ebs_manager.describe_volume(volume_id)
                if max_retries == 0:
                    volume_id = None
                if args.delete:
                    asg_ebs_manager.delete_volume(old_volume_id)
                    asg_ebs_manager.delete_snapshot(snapshot_id)
                az_diff = False
                
        # In this case , we cannot do anything other than creating a new volume
        if volume_id is None: 
            volume_id = asg_ebs_manager.create_volume(az,args.size,args.iops,args.throughput)
            max_retries = args.check_timeout
            volume = asg_ebs_manager.describe_volume(volume_id)
            while volume['State'] != 'available' and max_retries > 0:
                sleep(60)
                max_retries -= 1
                volume = asg_ebs_manager.describe_volume(volume_id)
            if max_retries == 0:
                volume_id = None


        # if we are able to create/ reuse old volume in the same az, attach the volume to the instance and tag it
        if volume_id is not None and not az_diff:
            volume_id = asg_ebs_manager.attach_volume(volume_id,instance_id,args.device)
            max_retries = args.check_timeout
            volume = asg_ebs_manager.describe_volume(volume_id)
            while volume['State'] != 'in-use' and max_retries > 0:
                sleep(60)
                max_retries -= 1
                volume = asg_ebs_manager.describe_volume(volume_id)
            if max_retries == 0:
                volume_id = None
            
            # if we are able to attach volume successfully to the instance, tag the volume 
            if volume_id is not None:
                asg_ebs_manager.tag_resource(volume_id)
                return

    # catch all 
    except Exception as e:
        print(f'Some error occurred :: {e}')

    # cleanup
    try:
        if snapshot_id:
            asg_ebs_manager.delete_snapshot(snapshot_id)
        if volume_id:
            asg_ebs_manager.delete_volume(volume_id)
    except Exception as e:
        pass
    
    # Exiting because we were not able to create or attach volume successfully
    exit(1)


