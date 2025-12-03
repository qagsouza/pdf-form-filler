from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = fh.read().splitlines()

setup(
    name="pdf-form-filler",
    version="0.2.0",
    author="Seu Nome",
    author_email="seu-email@exemplo.com",
    description="Preenchimento automático de formulários PDF",
    long_description=long_description,
    long_description_content_type="text/markdown",
    package_dir={"": "src"},  # Indica que os pacotes estão em src/
    packages=find_packages(where="src"),  # Procura pacotes em src/
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.7",
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'pdf-form-filler=pdf_form_filler.cli:main',
        ],
    },
    include_package_data=True,
)
