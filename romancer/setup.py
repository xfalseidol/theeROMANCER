from setuptools import setup, find_packages

setup(
    name='ROMANCER',
    version='0.1.0',
    description='ROMANCER',
    author='Your Name',
    author_email='your@email.com',
    packages=find_packages(),
    install_requires=[
        'matplotlib',
        'cartopy',
        'shapely',
        'dill',
        'numpy',
        'scipy',
        'pathlib',
        'setuptools',
        'pytest'
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3'
    ],
)
