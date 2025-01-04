from setuptools import find_packages, setup

def get_requirements():
    """
    Reads the requirements.txt file and returns a list of dependencies.
    """
    with open("requirements.txt", "r") as f:
        requirements = f.readlines()
    return [req.strip() for req in requirements if req.strip() and not req.startswith("#")]

setup(
    name="ai-oet-mentor",
    version="0.0.1",
    author="Jiya Mary Joseph",
    author_email="mejiyamaryjoseph@gmaail.com",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=get_requirements(),  # Read dependencies from requirements.txt
    python_requires=">=3.12",
)
