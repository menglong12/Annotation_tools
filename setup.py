from setuptools import setup

setup(
    name='PetkitAnnotationTool',
    version='1.0.0',
    packages=['config', 'core', 'modes', 'utils'],
    package_data={
        '': ['*.py'],
        'icons': ['*.png', '*.ico'],
    },
    include_package_data=True,
    entry_points={
        'console_scripts':[
            'annotation_tool=main:main',
        ],
    },
    install_requires=[
        'PyQt5>=5.15.0',
        'opencv-python>=4.2.0',
        'numpy>=1.19.0',
    ],
)





