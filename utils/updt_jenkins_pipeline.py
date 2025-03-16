import os
import xml.etree.ElementTree as ET
import html
import argparse

def update_jenkins_pipeline_script(config_path, jenkinsfile_path):
    """
    Updates the <script> section of a Jenkins job config.xml file using a Jenkinsfile.
    It replaces ' with &apos; and " with &quot; for proper XML encoding.
    
    :param config_path: Path to the config.xml file.
    :param jenkinsfile_path: Path to the Jenkinsfile containing the new pipeline script.
    """
    try:
        # Read the new pipeline script from the Jenkinsfile
        with open(jenkinsfile_path, "r", encoding="utf-8") as jenkinsfile:
            new_script_content = jenkinsfile.read()

        # Convert special characters: ' -> &apos;, " -> &quot;
        escaped_script_content = html.escape(new_script_content).replace("&#x27;", "&apos;")

        # Parse the XML file
        tree = ET.parse(config_path)
        root = tree.getroot()

        # Find the <script> element
        script_element = root.find(".//script")
        if script_element is not None:
            script_element.text = escaped_script_content
        else:
            print(f"Error: <script> element not found in {config_path}")
            return False

        # Convert the tree back to a string to remove unwanted `&amp;` occurrences
        xml_str = ET.tostring(root, encoding="utf-8", xml_declaration=True).decode("utf-8")

        # Remove every occurrence of `&amp;` from the XML string
        xml_str = xml_str.replace("&amp;", "&")

        # Write the cleaned XML back to the file
        with open(config_path, "w", encoding="utf-8") as file:
            file.write(xml_str)

        print(f"Updated pipeline script for {config_path}")
        return True

    except Exception as e:
        print(f"Error updating {config_path}: {e}")
        return False

def bulk_update_jenkins_pipelines(processor_folder, jenkinsfiles_folder):
    """
    Updates all Jenkins config.xml files in processor folders with the corresponding Jenkinsfile.

    :param processor_folder: Path to the folder containing processor-named subfolders with config.xml files.
    :param jenkinsfiles_folder: Path to the folder containing Jenkinsfiles named after processors.
    """
    # List all processor folders
    processor_names = [
        d
        for d in os.listdir(processor_folder)
        if os.path.isdir(os.path.join(processor_folder, d))
    ]

    for processor in processor_names:
        config_path = os.path.join(processor_folder, processor, 'config.xml')
        jenkinsfile_path = os.path.join(jenkinsfiles_folder, f'{processor}.Jenkinsfile')
        print(jenkinsfile_path)

        # Ensure both config.xml and Jenkinsfile exist
        if os.path.exists(config_path) and os.path.exists(jenkinsfile_path):
            print(f'Updating {processor} pipeline...')
            update_jenkins_pipeline_script(config_path, jenkinsfile_path)
        else:
            print(f'Skipping {processor}: Missing config.xml or Jenkinsfile.')


def main():
    """
    Main function that parses command-line arguments and runs the bulk update.
    """
    parser = argparse.ArgumentParser(
        description='Update Jenkins pipelines by replacing <script> content in config.xml with corresponding Jenkinsfiles.'
    )
    parser.add_argument(
        '-c',
        '--config',
        default='/jenkins/jenkins_home/jobs',
        help='Path to the folder containing processor-named subfolders with config.xml files.',
    )
    parser.add_argument(
        '-j',
        '--jenkins',
        default='/eda/processor_ci/jenkins_pipeline',
        help='Path to the folder containing Jenkinsfiles named after processors.',
    )

    args = parser.parse_args()
    configs_folder = args.config
    jenkinsfile_folder = args.jenkins

    # Run the bulk update function
    bulk_update_jenkins_pipelines(configs_folder, jenkinsfile_folder)


if __name__ == '__main__':
    main()
