import setuptools

setuptools.setup(
    name='nixvital-web-installer',
    version='0.3.1',
    description='The nixvital OS installer',
    author='Break Yang',
    author_email='breakds@gmail.com',
    packages=setuptools.find_packages(),
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'run_nixvital_installer=app.app:main',
        ],
    },
    python_requires='>=3.6',
)
