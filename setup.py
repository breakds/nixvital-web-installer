from setuptools import setup, find_packages

setup(
    name='nixvital-web-installer',
    version='0.4.0',
    description='The nixvital OS installer',
    author='Break Yang',
    author_email='breakds@gmail.com',
    # find_package() without any arguments will serach the same
    # directory as the setup.py for modules and packages.
    packages=find_packages(),
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'run_nixvital_installer=nixvital_installer.app:main',
        ],
    },
    python_requires='>=3.6',
)
