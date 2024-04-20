import argparse

from asgebsmanager.ebs_manager import manage_ebs

def main():
    parser = argparse.ArgumentParser("asgebsmanager",formatter_class=argparse.ArgumentDefaultsHelpFormatter,description="Manages the ebs volume in autoscaling environment")
    parser.add_argument("--asg-name",type=str,required=True,help="Name of the asg to be used as the tag to identify the volume to be attached")
    parser.add_argument("--region",type=str,default="ap-south-1",help="AWS region")
    parser.add_argument("--size",type=int,default=200,help="Size of the volume")
    parser.add_argument("--iops",type=int,default=3000,help="Iops of the volume")
    parser.add_argument("--throughput",type=int,default=125,help="Throughput of the volume")
    parser.add_argument("--fs-type",type=str,default="xfs",help="File system type")
    parser.add_argument("--device",type=str,default="/dev/xvdg",help="Device name to be used")
    parser.add_argument("--mount-point",type=str,default="/data",help="Mount Point path")
    parser.add_argument("--check-timeout",type=int,default=5,help="Timeout in minutes for each ebs api retry operation")
    parser.add_argument("--force",action='store_true',help="Set it to true, so that a new volume will be created if no existing volume is found")
    parser.add_argument("--delete",action='store_true',help="Set it to true, so that a old volume/snapshot will be deleted if a new volume is created from snapshot")

    args = parser.parse_args()

    manage_ebs(args)

if __name__ == '__main__':
    main()