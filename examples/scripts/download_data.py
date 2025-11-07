# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "array-record==0.6.0",
#     "click",
#     "tensorflow",
#     "tensorflow-datasets",
# ]
# ///
import click
import tensorflow_datasets as tfds


@click.group()
def cli():
    pass


@cli.command()
@click.argument("datasets", nargs=-1)
@click.option("--data-dir", envvar=["DIOPTRA_DATASETS_DIR", "TFDS_DATA_DIR"], help="datasets_dir")
@click.option("--dryrun", is_flag=True, help="datasets_dir")
def download(datasets: tuple[str, ...], data_dir: str | None, dryrun: bool):
    print(f"saving dataset(s) to {data_dir or '[tfds default location]'}")
    for dataset in datasets:
        print(f"  -- downloading and preparing {dataset}")
        if not dryrun:
            builder = tfds.builder(dataset, data_dir=data_dir)
            builder.download_and_prepare()
            # TODO: use array_records for better compatability with torch/jax.
            # this removes the requirement to have tensorflow installed after preparing the data.
            # It creates data sources instead of datasets so additional steps are required on load.
            # builder = tfds.builder(dataset, file_format="array_record")


@cli.command()
@click.option("--with-community", is_flag=True, help="include community datasets")
def list(with_community: bool):
    datasets = tfds.list_builders(with_community_datasets=with_community)
    print("\n".join(datasets))
    return datasets


def main():
    cli()


if __name__ == "__main__":
    cli.add_command(download)
    cli.add_command(list)
    main()
