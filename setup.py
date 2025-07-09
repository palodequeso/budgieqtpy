from setuptools import setup

setup(
    name="budgie",
    version="0.1",
    description="Budgie, a budget application for normies",
    packages=[".", "ui", "database", "scheduler"],
    include_package_data=True,
    install_requires=[
        "pyqt6",
        "sqlite3",
    ],
    entry_points={
        "console_scripts": [
            "budgie = budgie:main",
        ],
    },
)
