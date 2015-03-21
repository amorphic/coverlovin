from setuptools import setup

setup(
    name='CoverLovin',
    version='2.0.4',
    author='James Stewart',
    author_email='webmaster@jimter.net',
    packages=['coverlovin'],
    scripts=['bin/coverlovin'],
    url='https://launchpad.net/coverlovin/',
    description='Recursively parse audio files and download cover art.',
    long_description='Recursively process subdirectories of given directory, downloading appropriate cover images from Google Images if .mp3 files are found.',
    install_requires=[
        "simplejson >= 3.6.5",
        "mutagen >= 1.2.8",
    ],
)
