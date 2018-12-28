from setuptools import setup, find_packages


with open('requirements.txt') as f:
    required = f.read().splitlines()


setup(
    name='gcode-receiver',
    version='1.0',
    description='A very-dumb Gcode receiver for an integration test.',
    url='https://github.com/coddingtonbeear/gcode-receiver',
    author='Adam Coddington',
    author_email='me@adamcoddington.net',
    licence='MIT',
    packages=find_packages(),
    install_requires=required,
    entry_points={
        'console_scripts': [
            'gcode-receiver=gcode_receiver.cmdline:main'
        ]
    }
)
