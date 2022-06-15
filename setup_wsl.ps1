rm -rf .venv
python3 -m venv .venv --upgrade-deps
.venv/bin/Activate.ps1
pip install -U -r .tools/requirements/requirements_dev.txt
pip install -e .
pip install --force-reinstall /home/user/opencv-python/dist/opencv_contrib_python-4.6.0.66-cp310-cp310-linux_x86_64.whl
pre-commit install
pre-commit
