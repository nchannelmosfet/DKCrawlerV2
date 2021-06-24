from ipywidgets import Layout, HBox, Button, Textarea, Checkbox, Text
from IPython.display import display
from ipyfilechooser import FileChooser


def subcat_crawler_ui(location):
    btn_start = Button(
        description='Start Crawl',
        button_style='success',
    )
    btn_combine_data = Button(
        description='Combine Data',
        button_style='success',
    )
    text_area_urls = Textarea(
        placeholder='Enter URLs here, 1 per line',
        layout=Layout(
            overflow_x='scroll',
            width='auto',
            height='100px',
            flex_direction='row',
            display='flex',
        )
    )
    box_headless = Checkbox(
        value=True,
        description='Headless',
        indent=False,
    )
    text_session_name = Text(
        value=None,
        placeholder='Optional session name',
        indent=False,
    )
    btn_hbox = HBox([btn_start, btn_combine_data, box_headless])
    params_hbox = HBox([text_session_name])

    file_chooser = FileChooser(
        path=location,
        title="Location to download data",
        show_only_dirs=True,
        select_default=True
    )
    display(btn_hbox, params_hbox, file_chooser, text_area_urls)
