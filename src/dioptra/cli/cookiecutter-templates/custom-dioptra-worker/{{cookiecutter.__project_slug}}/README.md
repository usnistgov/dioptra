# {{ cookiecutter.project_name }}

This is a custom Dioptra worker container project generated from the Dioptra cookiecutter template.

## Quick start

1. Edit `requirements.txt` to add the Python packages your worker needs. Keep `dioptra-platform` as a dependency.
2. Build the Docker image:

   ```sh
   docker build -t {{ cookiecutter.__project_slug }}:dev .
   ```

3. Integrate the image into your Dioptra deployment using a Docker Compose override file.

## What's in this folder

| File / Directory   | Purpose                                                |
| ------------------ | ------------------------------------------------------ |
| `Dockerfile`       | Multi-stage build that produces the worker image       |
| `requirements.txt` | Python packages to install in the worker environment   |
| `ca-certificates/` | Optional custom CA certificates for the build process  |
| `configs/`         | Configuration files copied into the image (AWS config) |
| `shellscripts/`    | Shell script templates compiled during the build       |

## Documentation

For detailed instructions, see the Dioptra documentation:

- [Create a Custom Worker Container](https://pages.nist.gov/dioptra/how-to/setup-dioptra/configure-setup/creating-custom-workers.html) (how-to guide)
- [Custom Worker Template Reference](https://pages.nist.gov/dioptra/how-to/setup-dioptra/reference/custom-worker-template-reference.html) (template variables and folder structure)
- [Integrate Custom Containers](https://pages.nist.gov/dioptra/how-to/setup-dioptra/configure-setup/integrating-custom-containers.html) (adding the worker to your deployment)
