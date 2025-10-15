from processor_ci_utils.labeler.src import main as labeler_main

def create_makefile(processor_name):
    labeler_main.core_labeler(
        directory="processors/" + processor_name,
        config_file="config/"   ,
        output_dir="processor_ci_utils/Makefiles",
        top_dir="rtl/"
    )