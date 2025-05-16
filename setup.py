from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

with open("requirements.txt", "r", encoding="utf-8") as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name="hey-helper",
    version="0.1.1",
    description="Ask a question, get an answer—right in your terminal.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Vikrant Singh Chauhan",
    packages=find_packages(),
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "hey = hey_helper.main:main",
        ],
    },
    python_requires=">=3.8",
    url="https://o.eval.blog/hey",
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    include_package_data=True,
)
