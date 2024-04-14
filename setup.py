from setuptools import setup, find_packages
import os 

setup(
    name = 'asgebsmanager',
    version = "1.3",
    author = 'Raghav Gupta',
    description = 'AWS Asg ebs manager',
    packages = find_packages("src"),
    package_dir= {
        "asgebsmanager": os.path.join("src","asgebsmanager")
    },
    install_requires = [
        "boto3==1.34.84",
        "botocore==1.34.84",
        "certifi==2024.2.2",
        "charset-normalizer==3.3.2",
        "idna==3.7",
        "jmespath==1.0.1",
        "python-dateutil==2.9.0.post0",
        "requests==2.31.0",
        "s3transfer==0.10.1",
        "six==1.16.0",
        "urllib3"
    ],
    classifiers=[
        "Programming Language :: Python :: 3"
    ],
    entry_points = {'console_scripts': ['asgebsmanager = asgebsmanager.__main__:main'],}
)