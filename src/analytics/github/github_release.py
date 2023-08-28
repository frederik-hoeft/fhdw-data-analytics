import os
import requests
import tqdm

class GitHubRelease:
    __repository_id: int

    def __init__(self, repository_id: int) -> None:
        self.__repository_id = repository_id

    def pull_latest_artifact(self, artifact_name: str, target_dir: str) -> None:
        print(f'Checking for new version of GitHub artifact \'{artifact_name}\'...')
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)
        version_file = os.path.join(target_dir, artifact_name + '.version')
        if not os.path.exists(version_file):
            with open(version_file, 'w') as f:
                f.write('1970-01-01T00:00:00Z')
        # check if there is a newer version available
        with open(version_file, 'r') as f:
            current_version = f.read()
        r = requests.get(f'https://api.github.com/repositories/{self.__repository_id}/releases/latest')
        # compare dates, and extract download link for artifact if there is a newer version available
        json = r.json()
        latest_version = json['published_at']
        if latest_version > current_version:
            print(f'Pulling new version of \'{artifact_name}\' from {json["html_url"]}. ({latest_version} over {current_version})')
            download_link = None
            expected_size = None
            for asset in json['assets']:
                if asset['name'] == artifact_name:
                    download_link = asset['browser_download_url']
                    expected_size = int(asset['size'])
            if download_link is None:
                raise Exception(f'Could not find download link for \'{artifact_name}\'. Check the GitHub release')
            # download artifact
            r = requests.get(download_link, stream=True)
            with open(os.path.join(target_dir, artifact_name), 'wb') as f:
                bar_format = '{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}{postfix}]'
                with tqdm.tqdm(total=expected_size, unit='B', unit_scale=True, unit_divisor=1024, bar_format=bar_format) as pbar:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                        pbar.update(len(chunk))
            # update version file
            with open(version_file, 'w') as f:
                f.write(json['published_at'])
            print('Successfully updated artifact')
        else:
            print(f'Artifact \'{artifact_name}\' is up to date ({current_version})')