from setuptools import setup, find_packages
import os 

setup(
    name = 'asgebsmanager',
    version = "1.5.3",
    author = 'Raghav Gupta',
    description = 'AWS Asg ebs manager',
    packages = find_packages("src"),
    package_dir= {
        "asgebsmanager": os.path.join("src","asgebsmanager")
    },
    install_requires = [
        "boto3",
        "botocore",
        "certifi",
        "charset-normalizer",
        "idna",
        "jmespath",
        "python-dateutil",
        "requests",
        "s3transfer",
        "six",
        "urllib3"
    ],
    classifiers=[
        "Programming Language :: Python :: 3"
    ],
    entry_points = {'console_scripts': ['asgebsmanager = asgebsmanager.__main__:main'],}
)