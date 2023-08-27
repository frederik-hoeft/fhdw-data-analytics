import os
import requests
import tqdm

class RankingsDBUpdater:
    @staticmethod
    def update_rankings_db(target_dir: str) -> None:
        version_file = os.path.join(target_dir, 'rankings.db.version')
        db_file = os.path.join(target_dir, 'rankings.db')
        print('Checking for new database version...')
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)
        if not os.path.exists(version_file):
            with open(version_file, 'w') as f:
                f.write('1970-01-01T00:00:00Z')
        # check if there is a newer version available
        with open(version_file, 'r') as f:
            current_version = f.read()
        r = requests.get('https://api.github.com/repositories/668823738/releases/latest')
        # compare dates, and extract download link for 'rankings.db' asset if there is a newer version available
        json = r.json()
        latest_version = json['published_at']
        if latest_version > current_version:
            print('New version available ({} --> {}). Updating...'.format(current_version, latest_version))
            download_link = None
            expected_size = None
            for asset in json['assets']:
                if asset['name'] == 'rankings.db':
                    download_link = asset['browser_download_url']
                    expected_size = int(asset['size'])
            if download_link is None:
                raise Exception('Could not find download link for rankings.db asset')
            # download rankings.db
            r = requests.get(download_link, stream=True)
            with open(db_file, 'wb') as f:
                bar_format = '{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}{postfix}]'
                with tqdm.tqdm(total=expected_size, unit='B', unit_scale=True, unit_divisor=1024, bar_format=bar_format) as pbar:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                        pbar.update(len(chunk))
            # update version file
            with open(version_file, 'w') as f:
                f.write(json['published_at'])
            print('Done')
        else:
            print('Version {} is already the latest version'.format(current_version))