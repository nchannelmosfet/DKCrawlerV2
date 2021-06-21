py -3.9-64 -m pip install virtualenv
py -3.9-64 -m virtualenv venv
.\venv\Scripts\activate
pip install -r requirements.txt
playwright install

jupyter nbextension enable --py widgetsnbextension
jupyter labextension install @jupyter-widgets/jupyterlab-manager
jupyter lab build
