Developers Guide
- Install python v3.8.2
- Upgrade pip & Install dependancies
  - python -m pip install --upgrade pip
  - pip install flake8
  - pip install -r requirements.txt
  
- Steps prior pull request
  - Lint with flake8
    - flake8 . --count --show-source --statistics # exit-zero treats all errors as warnings.
  
