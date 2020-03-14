import setuptools

setuptools.setup(
    name='nixvital-web-installer',
    version='0.3.0',
    description='The nixvital OS installer',
    author='Break Yang',
    author_email='breakds@gmail.com',
    packages=setuptools.find_packages(),
    entry_points={
        'console_scripts': [
            'nixvital_install=app.app:main',
        ],
    },
    python_requires='>=3.6',
)
