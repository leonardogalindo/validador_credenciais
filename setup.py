#!/usr/bin/env python3
"""Setup script para o Validador de Credenciais Locaweb.

Este script configura o projeto como um pacote Python instalável,
permitindo instalação via pip e criando comandos de console.
Segue as diretrizes estabelecidas no GEMINI.md.
"""

from pathlib import Path

from setuptools import find_packages, setup

# Lê o conteúdo do README para a descrição longa
readme_file = Path(__file__).parent / "README.md"
long_description = ""
if readme_file.exists():
    long_description = readme_file.read_text(encoding="utf-8")

# Lê as dependências do requirements.txt
requirements_file = Path(__file__).parent / "requirements.txt"
install_requires = []
if requirements_file.exists():
    with open(requirements_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            # Ignora comentários e linhas vazias
            if line and not line.startswith("#"):
                # Remove comentários inline
                if "#" in line:
                    line = line.split("#")[0].strip()
                install_requires.append(line)

# Separa dependências de produção das de desenvolvimento
production_deps = []
dev_deps = []
test_deps = []

for dep in install_requires:
    if any(test_pkg in dep.lower() for test_pkg in ["pytest", "coverage", "mock"]):
        test_deps.append(dep)
    elif any(
        dev_pkg in dep.lower() for dev_pkg in ["black", "isort", "flake8", "mypy"]
    ):
        dev_deps.append(dep)
    else:
        production_deps.append(dep)

setup(
    # Informações básicas do pacote
    name="validador-credenciais",
    version="1.0.0",
    description="Sistema de validação de credenciais via API da Locaweb",
    long_description=long_description,
    long_description_content_type="text/markdown",
    # Informações do autor
    author="Leonardo Galindo",
    author_email="leonardo@exemplo.com",
    # URLs do projeto
    url="https://github.com/leonardogalindo/validador-credenciais",
    project_urls={
        "Bug Reports": "https://github.com/leonardogalindo/validador-credenciais/issues",
        "Source": "https://github.com/leonardogalindo/validador-credenciais",
        "Documentation": "https://github.com/leonardogalindo/validador-credenciais/blob/main/README.md",
    },
    # Configuração de pacotes
    packages=find_packages(exclude=["tests*", "docs*"]),
    py_modules=["main"],  # Inclui o main.py como módulo
    # Dependências
    install_requires=production_deps,
    extras_require={
        "dev": dev_deps,
        "test": test_deps,
        "all": dev_deps + test_deps,
    },
    # Requisitos de Python
    python_requires=">=3.8",
    # Classificadores para PyPI
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Topic :: Security",
        "Topic :: System :: Systems Administration",
        "Topic :: Utilities",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    # Palavras-chave
    keywords="security, credentials, validation, locaweb, api, csv, batch",
    # Ponto de entrada para comando de console
    entry_points={
        "console_scripts": [
            "validar-credenciais=main:main",
        ],
    },
    # Arquivos de dados incluídos
    include_package_data=True,
    package_data={
        "": ["*.md", "*.txt", "*.ini", "*.env.example"],
    },
    # Configurações adicionais
    zip_safe=False,  # Permite acesso a arquivos de dados
    # Licença
    license="MIT",
)
