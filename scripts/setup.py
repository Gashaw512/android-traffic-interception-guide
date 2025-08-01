from setuptools import setup

setup(
    name='burpdrop',
    version='1.1.0',
    description='Easy Burp Suite Certificate Installer for Android',
    author='Your Name',
    author_email='kidanugashaw@gmail.com',
    url='https://github.com/Gashaw512/android-traffic-interception-guide',
    py_modules=['burpDrop'],
    install_requires=[
        'colorama',
        'requests'
    ],
    entry_points={
        'console_scripts': [
            'burpdrop=burpDrop:main',
        ],
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
)