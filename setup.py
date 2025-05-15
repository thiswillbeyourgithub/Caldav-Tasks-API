from setuptools import setup, find_packages

setup(
    name="caldav-tasks-api",
    version="1.1.0",
    author="thiswillbeyourgithub",
    description="A Python client for CalDAV task servers, with a CLI.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/thiswillbeyourgithub/CaldavTasksAPI/",
    keywords=[
        "caldav",
        "tasks",
        "vtodo",
        "todo",
        "cli",
        "api",
        "nextcloud",
        "calendar",
        "task management",
    ],
    packages=find_packages(include=["caldav_tasks_api", "caldav_tasks_api.*"]),
    install_requires=[
        "caldav>=1.4.0",
        "click>=8.1.8",
        "urllib3>=2.4.0",
        "loguru>=0.7.0",
        "platformdirs>=3.0.0",
    ],
    extras_require={
        "dev": [
            "dotenv>=0.9.9",
            "black>=25.1.0",
            "twine>=6.1.0",
            "build>=1.2.2.post1",
            "bumpver>=2024.1130",
            "pytest>=8.3.5",
            "pre-commit>=4.2.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "caldav-tasks-api=caldav_tasks_api.__main__:cli",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Topic :: Utilities",
    ],
    python_requires=">=3.8",
)
