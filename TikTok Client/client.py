import requests
import scriptwrapper
import ftplib
import settings
import clientUI
import traceback, sys

settings.generateConfigFile()
httpaddress = f"{settings.address}:{settings.HTTP_PORT}"
max_progress = None
current_progress = None
render_message = None
music_categories = ["None"]
mainMenuWindow = None

from time import sleep

def requestGames():
    responsegames =requests.get(f'http://{httpaddress}/getgames')
    clientUI.games = responsegames.json()["games"]

def requestClips(game, amount, window):
    r = requests.get(f'http://{httpaddress}/getclips', json={"game": game, "amount" : int(amount)},  headers={'Accept-Encoding': None})
    clips = r.json()["clips"]
    clipwrappers = []

    for clip in clips:
        id = clip["id"]
        mp4 = clip["mp4"]
        streamer = clip["author_name"]
        duration = clip["duration"]
        clip_title = clip["clip_title"]
        diggCount = clip["diggCount"]
        shareCount = clip["shareCount"]
        playCount = clip["playCount"]
        commentCount = clip["commentCount"]
        clipwrappers.append(scriptwrapper.DownloadedTwitchClipWrapper(id, streamer, clip_title, mp4, duration, diggCount, shareCount, playCount, commentCount))


    window.set_max_progres_bar.emit(len(clips))

    ftp = ftplib.FTP()
    ftp.connect(settings.address, settings.FTP_PORT)
    ftp.login(settings.FTP_USER, settings.FTP_PASSWORD)
    ftp.cwd('/VideoFiles/')
    bad_indexes = []
    for i, clip in enumerate(clipwrappers):
        try:
            mp4 = clip.mp4
            print(f"Downloading {i + 1}/{len(clipwrappers)} clips {mp4}")
            with open(f"TempClips/{mp4}.mp4", 'wb') as file:
                ftp.retrbinary(f'RETR {mp4}.mp4', file.write)
            window.update_progress_bar.emit(i + 1)
        except Exception as e:
            bad_indexes.append(i)
            print("Failed to download clip, will remove later.")
            print(e)

    for i in sorted(bad_indexes, reverse=True):
        del clipwrappers[i]

    vidwrapper = scriptwrapper.ScriptWrapper(clipwrappers)
    window.finished_downloading.emit(vidwrapper)

def testFTPConnection(username, password):
    try:
        ftp = ftplib.FTP()
        ftp.connect(settings.address, settings.FTP_PORT)
        ftp.login(username, password)
        return True
    except Exception as e:
        return False



def requestClipsWithoutClips(game, amount, clips, window):
    ids = [str(clip.id) for clip in clips]
    r = requests.get(f'http://{httpaddress}/getclipswithoutids', json={"game": game, "amount" : int(amount), "ids" : ids},  headers={'Accept-Encoding': None})
    clips = r.json()["clips"]
    clipwrappers = []
    for clip in clips:
        id = clip["id"]
        mp4 = clip["mp4"]
        streamer = clip["author_name"]
        duration = clip["duration"]
        clip_title = clip["clip_title"]
        diggCount = clip["diggCount"]
        shareCount = clip["shareCount"]
        playCount = clip["playCount"]
        commentCount = clip["commentCount"]
        clipwrappers.append(scriptwrapper.DownloadedTwitchClipWrapper(id, streamer, clip_title, mp4, duration, diggCount, shareCount, playCount, commentCount))

    window.set_max_progres_bar.emit(len(clips))

    ftp = ftplib.FTP()
    ftp.connect(settings.address, settings.FTP_PORT)
    ftp.login(settings.FTP_USER, settings.FTP_PASSWORD)
    ftp.cwd('/VideoFiles/')
    bad_indexes = []

    for i, clip in enumerate(clipwrappers):
        try:
            mp4 = clip.mp4
            print(f"Downloading {i + 1}/{len(clipwrappers)} clips {mp4}")
            with open(f"TempClips/{mp4}.mp4", 'wb') as file:
                ftp.retrbinary(f'RETR {mp4}.mp4', file.write, blocksize=settings.block_size)
            window.update_progress_bar.emit(i + 1)
        except Exception as e:
            bad_indexes.append(i)
            print("Failed to download clip, will remove later.")
            print(e)

    for i in sorted(bad_indexes, reverse=True):
        del clipwrappers[i]

    vidwrapper = scriptwrapper.ScriptWrapper(clipwrappers)
    window.finished_downloading.emit(vidwrapper)

def uploadFile(location, ftplocation, name):
    ftp = ftplib.FTP()
    ftp.connect(settings.address, settings.FTP_PORT)
    ftp.login(settings.FTP_USER, settings.FTP_PASSWORD)
    ftp.cwd(f'{ftplocation}')
    with open(location,'rb') as file:
        ftp.storbinary(f'STOR {name}', file, blocksize=262144)

def VideoGeneratorRenderStatus():
    global max_progress, current_progress, render_message, music_categories
    while True:
        if mainMenuWindow is not None:
            try:
                r = requests.get(f'http://{httpaddress}/getrenderinfo',  headers={'Accept-Encoding': None})
                renderData = r.json()
                mainMenuWindow.update_render_progress.emit(renderData)
            except Exception:
                print("server not online")
                traceback.print_exc(file=sys.stdout)

        sleep(5)


def exportVideo(videowrapper, name, window):

    clips = videowrapper.final_clips

    introUpload = None
    vidClipUpload = None

    amount = sum(1 for clip in clips if clip.upload)
    window.set_max_progres_bar.emit(amount)

    for clip in clips:
        if clip.upload:
            introUpload = clip.mp4
            name = len(clip.mp4.split("/"))
            new_name = (clip.mp4.split("/")[name-1]).replace(".mp4", "")
            clip.mp4 = f"UploadedFiles/{new_name}.mp4"
            uploadFile(introUpload, "/UploadedFiles/", f"{new_name}.mp4")
            window.update_progress_bar.emit()
            continue


    clipInfo = [
        {
            "id": clip.id,
            "isIntro": clip.isIntro,
            "isUpload": clip.upload,
            "mp4": clip.mp4,
            "duration": clip.vid_duration,
            "audio": clip.audio,
            "keep": clip.isUsed,
            "isInterval": clip.isInterval,
            "isOutro": clip.isOutro,
        }
        for clip in clips
    ]
    window.update_progress_bar.emit()

    info = {"clips": clipInfo, "name" : name}
    r = requests.get(f'http://{httpaddress}/uploadvideo', json=info,  headers={'Accept-Encoding': None})
    sucess = r.json()["upload_success"]
    print("Uploaded Video!")
    window.finished_downloading.emit()


def requestFinishedVideoList(window):
    r = requests.get(f'http://{httpaddress}/getfinishedvideoslist',  headers={'Accept-Encoding': None})
    videos = r.json()["videos"]
    window.download_finished_videos_names.emit(videos)

def downloadFinishedVideo(name, window):
    ftp = ftplib.FTP()
    ftp.connect(settings.address, settings.FTP_PORT)
    ftp.login(settings.FTP_USER, settings.FTP_PASSWORD)
    ftp.cwd('/FinalVideos/')

    print(f"Downloading Video {name} ")
    with open(f"Finished Videos/{name}.mp4", 'wb') as file:
        print(f'{name}.mp4')
        ftp.retrbinary(f'RETR {name}.mp4', file.write, blocksize=settings.block_size)
    window.update_progress_bar.emit(1)
    with open(f"Finished Videos/{name}.txt", 'wb') as file:
        ftp.retrbinary(f'RETR {name}.txt', file.write, blocksize=settings.block_size)
    window.update_progress_bar.emit(2)
    window.finish_downloading.emit()


