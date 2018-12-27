from setuptools import setup, find_packages


setup(
    name='gcode-receiver',
    version='0.1',
    description='A very-dumb Gcode receiver for an integration test.',
    url='https://github.com/coddingtonbeear/gcode-receiver',
    author='Adam Coddington',
    author_email='me@adamcoddington.net',
    licence='MIT',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'gcode-receiver=gcode_receiver.cmdline:main'
        ]
    }
)
