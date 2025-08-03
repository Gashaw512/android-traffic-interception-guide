from setuptools import setup, find_packages
import os

this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

with open(os.path.join(this_directory, 'scripts', 'requirements.txt'), encoding='utf-8') as f:
    requirements = f.read().splitlines()

setup(
    name='burpdrop',
    version='1.1.0',
    author='Gashaw Kidanu',
    author_email='kidanugashaw@gmail.com',
    description='A cross-platform Burp Suite CA Certificate installer for Android devices',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/Gashaw512/android-traffic-interception-guide',
    
    packages=find_packages(),
    
    package_data={
        'scripts': ['config.json'],
    },
    include_package_data=True,
    
    install_requires=requirements,
    
    entry_points={
        'console_scripts': [
            'burpdrop=scripts.main:main',
        ],
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Security',
        'Topic :: Utilities',
    ],
    python_requires='>=3.7',
    keywords='android burpsuite certificate installer root magisk interception security',
)