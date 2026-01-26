from setuptools import setup, find_packages

setup(
    name="nlp-defender",
    version="1.0",
    packages=find_packages(),
    install_requires=[
        'numpy',
        'scipy',
        'spacy',
        'textstat',
        'pyyaml'
    ],
    entry_points={
        'console_scripts': [
            'nlp-defender=cli:main',
        ],
    },
)
