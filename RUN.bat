@echo off
:: Change to the directory of this script
cd /d "%~dp0"
title VideoFactory - Reel Generator
color 0A

:: Determine Python executable
set "PY=python"
if exist "venv\Scripts\python.exe" (
    echo [Info] Using local virtual environment (venv)...
    set "PY=venv\Scripts\python.exe"
) else (
    echo [Warning] Virtual environment not found. Using system Python...
)

:: Auto-activate virtual environment if it exists (for path variables and tools)
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

:MENU
cls
echo.
echo ================================================================
echo                V I D E O   F A C T O R Y
echo            Automated Reel Generator System
echo ================================================================
echo.
echo   QUICK GENERATE:
echo.
echo   [1]  Gospel Reel              [Random AI script]
echo   [2]  Prayer Reel              [Powerful prayer]
echo   [3]  Praise Reel              [Worship energy]
echo   [4]  Motivational Reel        [Hard truths]
echo   [5]  Bedtime Whisper          [Soft sleep prayer]
echo   [6]  Swahili Reel             [Pure Swahili]
echo.
echo   ADVANCED:
echo.
echo   [7]  Viral Hook Reel          [God told me...]
echo   [8]  Time-Based Auto          [Picks by time]
echo   [9]  Batch Generate (3)
echo   [10] Batch Generate (10)
echo.
echo   ** TRENDING - CHRISTIAN FOCUS **:
echo.
echo   [11] Trending Christian Reel  [Any Christian news]
echo   [12] Church News Reel         [Megachurches, pastors]
echo   [13] Gospel Artist Reel       [Christian musicians]
echo   [14] Christian Celebrity      [Famous faith stories]
echo   [15] Revival/Crusade Reel     [Awakening news]
echo   [16] Persecution Reel         [Christians attacked]
echo   [17] African Christian Reel   [Kenya/Tz church news]
echo   [18] Moral Issue Reel         [Family, values]
echo.
echo   ** TRENDING - WORLD ANGLE **:
echo.
echo   [19] Trending Sports Angle    [Victory verses]
echo   [20] Trending Tragedy Angle   [Comfort verses]
echo   [21] Trending Swahili Reel    [Habari za leo]
echo   [22] Show Current Trends      [Browse what's hot]
echo   [23] Refresh Trend Cache      [Fetch fresh news]
echo.
echo   DOWNLOAD STOCK MEDIA:
echo.
echo   [24] Download Pinterest Media [Get high-res images & videos]
echo   [25] Download Pexels Stock    [Get vertical videos]
echo   [26] Download Background Music [Get MP3 beats from YouTube]
echo.
echo   SERIES + SONGS:
echo.
echo   [27] Armor of God Series
echo   [28] Powerful Prayers Series
echo   [29] Random Song to Reel
echo   [30] Pick Specific Song
echo   [31] List All Songs
echo.
echo   TOOLS:
echo.
echo   [32] Daily Trends Brief       [8-territory report]
echo   [33] Open Output Folder
echo   [34] Open Songs Folder
echo   [35] Web Control Dashboard
echo   [36] Run Auto-Publishing Pipeline
echo.
echo   LONGFORM CLIPPER:
echo.
echo   [37] Clip Long Video          [Sermon/podcast -^> shorts]
echo.
echo   [0]  Exit
echo.
echo ================================================================
set /p choice="  Enter your choice [0-37]: "

set PYTHONPATH=%CD%

if "%choice%"=="1"  "%PY%" main.py --ai --niche gospel
if "%choice%"=="2"  "%PY%" main.py --ai --niche prayer
if "%choice%"=="3"  "%PY%" main.py --ai --niche praise
if "%choice%"=="4"  "%PY%" main.py --ai --niche motivational
if "%choice%"=="5"  "%PY%" main.py --ai --niche bedtime_prayer
if "%choice%"=="6"  "%PY%" main.py --ai --niche swahili --lang swahili
if "%choice%"=="7"  "%PY%" main.py --ai --viral
if "%choice%"=="8"  "%PY%" main.py --time-based
if "%choice%"=="9"  "%PY%" main.py --batch 3 --viral
if "%choice%"=="10" "%PY%" main.py --batch 10 --viral
if "%choice%"=="11" "%PY%" main.py --trending --niche gospel
if "%choice%"=="12" "%PY%" main.py --trending --niche gospel --trend-category church_news
if "%choice%"=="13" "%PY%" main.py --trending --niche gospel --trend-category gospel_music
if "%choice%"=="14" "%PY%" main.py --trending --niche gospel --trend-category christian_celeb
if "%choice%"=="15" "%PY%" main.py --trending --niche gospel --trend-category revival
if "%choice%"=="16" "%PY%" main.py --trending --niche gospel --trend-category persecution
if "%choice%"=="17" "%PY%" main.py --trending --niche gospel --trend-category african_church
if "%choice%"=="18" "%PY%" main.py --trending --niche gospel --trend-category moral_issue
if "%choice%"=="19" "%PY%" main.py --trending --niche gospel --trend-category sports
if "%choice%"=="20" "%PY%" main.py --trending --niche gospel --trend-category tragedy
if "%choice%"=="21" "%PY%" main.py --trending --niche swahili --lang swahili
if "%choice%"=="22" goto SHOW_TRENDS
if "%choice%"=="23" goto REFRESH_TRENDS
if "%choice%"=="24" goto DOWNLOAD_PINTEREST
if "%choice%"=="25" goto DOWNLOAD_PEXELS
if "%choice%"=="26" goto DOWNLOAD_MUSIC
if "%choice%"=="27" "%PY%" main.py --series armor_of_god
if "%choice%"=="28" "%PY%" main.py --series powerful_prayers
if "%choice%"=="29" "%PY%" main.py --song random
if "%choice%"=="30" goto PICK_SONG
if "%choice%"=="31" goto LIST_SONGS
if "%choice%"=="32" "%PY%" mwijay_daily_brief.py
if "%choice%"=="33" explorer output\videos
if "%choice%"=="34" explorer assets\songs
if "%choice%"=="35" goto WEB_DASHBOARD
if "%choice%"=="36" goto RUN_PUBLISHER
if "%choice%"=="37" goto CLIP_LONGFORM
if "%choice%"=="0"  exit

echo.
echo ================================================================
echo                     DONE!
echo ================================================================
echo.
pause
goto MENU

:CLIP_LONGFORM
cls
echo ================================================================
echo             LONGFORM CLIPPER (LONG VIDEO - SHORTS)
echo ================================================================
echo.
"%PY%" main.py --clip-list
echo.
set /p clipfile="Enter video file name or full path: "
if "%clipfile%"=="" goto MENU
set /p clipcount="How many clips? [3]: "
if "%clipcount%"=="" set clipcount=3
"%PY%" main.py --clip-longform "%clipfile%" --clips %clipcount%
echo.
pause
goto MENU

:SHOW_TRENDS
cls
"%PY%" -c "from src.scripts.trending_topics import TrendCollector; TrendCollector().show_trends_summary()"
pause
goto MENU

:REFRESH_TRENDS
cls
echo Fetching fresh trends from internet...
"%PY%" -c "import asyncio; from src.scripts.trending_topics import TrendCollector; asyncio.run(TrendCollector().collect_all_trends())"
pause
goto MENU

:LIST_SONGS
cls
"%PY%" -c "from src.audio.song_picker import list_songs_pretty; list_songs_pretty()"
pause
goto MENU

:PICK_SONG
cls
"%PY%" -c "from src.audio.song_picker import list_songs_pretty; list_songs_pretty()"
echo.
set /p songname="Enter part of song name: "
set /p songlang="Language [en/sw] (or Enter for auto): "
if "%songlang%"=="" (
    "%PY%" main.py --song "%songname%"
) else (
    "%PY%" main.py --song "%songname%" --lang %songlang%
)
pause
goto MENU

:DOWNLOAD_PINTEREST
cls
echo ================================================================
echo             DOWNLOAD PINTEREST MEDIA (IMAGES & VIDEOS)
echo ================================================================
echo.
echo   Select target folder to download into:
echo   [1] gospel            (saves to pinterest\gospel)
echo   [2] jesus             (saves to pinterest\jesus)
echo   [3] backgrounds       (saves to pinterest\backgrounds)
echo   [4] nature_pics       (saves to pinterest\nature_pics)
echo   [5] people            (saves to pinterest\people)
echo   [6] quotes            (saves to pinterest\quotes)
echo   [7] characters        (saves to pinterest\characters\character_name)
echo.
set /p pin_folder_choice="  Enter target folder [1-7]: "

set pin_folder=pinterest\gospel
if "%pin_folder_choice%"=="1" set pin_folder=pinterest\gospel
if "%pin_folder_choice%"=="2" set pin_folder=pinterest\jesus
if "%pin_folder_choice%"=="3" set pin_folder=pinterest\backgrounds
if "%pin_folder_choice%"=="4" set pin_folder=pinterest\nature_pics
if "%pin_folder_choice%"=="5" set pin_folder=pinterest\people
if "%pin_folder_choice%"=="6" set pin_folder=pinterest\quotes
if "%pin_folder_choice%"=="7" (
    echo.
    set /p char_name="  Enter character name (e.g. samson, david, mary): "
    set pin_folder=pinterest\characters\%char_name%
)

echo.
echo   Select download source:
echo   [1] Predefined Board (Auto-matches your folder)
echo   [2] Custom Pinterest URL (Board or specific Pin link)
echo.
set /p pin_source="  Enter option [1-2]: "

if "%pin_source%"=="1" (
    set pin_target=gospel
    if "%pin_folder_choice%"=="1" set pin_target=gospel
    if "%pin_folder_choice%"=="2" set pin_target=gospel
    if "%pin_folder_choice%"=="3" set pin_target=tech
    if "%pin_folder_choice%"=="4" set pin_target=nature
    if "%pin_folder_choice%"=="5" set pin_target=prayer
    if "%pin_folder_choice%"=="6" set pin_target=quotes
    if "%pin_folder_choice%"=="7" (
        echo.
        echo Predefined source not available for custom characters.
        echo Please use Custom Board URL option or Pexels search.
        echo.
        pause
        goto MENU
    )
    "%PY%" main.py --download-pinterest "%pin_target%" --download-folder "%pin_folder%" --download-limit 15
)
if "%pin_source%"=="2" (
    echo.
    set /p board_url="  Enter Pinterest Board or Pin URL: "
    "%PY%" main.py --download-pinterest "%board_url%" --download-folder "%pin_folder%" --download-limit 15
)
pause
goto MENU

:DOWNLOAD_PEXELS
cls
echo ================================================================
echo             DOWNLOAD PEXELS STOCK MEDIA
echo ================================================================
echo.
echo   Select media type to download:
echo   [1] Vertical Videos  (saves to assets\stock\<folder>)
echo   [2] Portrait Photos  (saves to assets\stock\<folder>)
echo.
set /p pexels_type_choice="  Enter option [1-2]: "
set pexels_type=video
if "%pexels_type_choice%"=="2" set pexels_type=photo

echo.
set /p pexels_query="  Enter search term (e.g. nature, david bible, samson): "
set /p pexels_folder="  Enter folder name (gospel, nature, pinterest\characters\samson) [nature]: "
if "%pexels_folder%"=="" set pexels_folder=nature

set /p pexels_limit="  Enter number of files to download [5]: "
if "%pexels_limit%"=="" set pexels_limit=5

"%PY%" main.py --download-stock "%pexels_query%" --download-type %pexels_type% --download-limit %pexels_limit% --download-folder "%pexels_folder%"
pause
goto MENU

:DOWNLOAD_MUSIC
cls
echo ================================================================
echo             DOWNLOAD BACKGROUND MUSIC / BEATS
echo ================================================================
echo.
echo   Select target niche music folder:
echo   [1] gospel/worship   (saves to assets\music\gospel)
echo   [2] prayer/ambient   (saves to assets\music\prayer)
echo   [3] praise/cheerful  (saves to assets\music\praise)
echo   [4] motivational     (saves to assets\music\motivational)
echo   [5] tech/cinematic   (saves to assets\music\tech)
echo   [6] swahili          (saves to assets\music\swahili)
echo   [7] custom query     (saves to assets\music\general)
echo.
set /p music_choice="  Enter target folder [1-7]: "

set music_folder=general
set music_target=gospel
if "%music_choice%"=="1" (
    set music_folder=gospel
    set music_target=gospel
)
if "%music_choice%"=="2" (
    set music_folder=prayer
    set music_target=prayer
)
if "%music_choice%"=="3" (
    set music_folder=praise
    set music_target=praise
)
if "%music_choice%"=="4" (
    set music_folder=motivational
    set music_target=motivational
)
if "%music_choice%"=="5" (
    set music_folder=tech
    set music_target=tech
)
if "%music_choice%"=="6" (
    set music_folder=swahili
    set music_target=swahili
)
if "%music_choice%"=="7" (
    echo.
    set /p custom_query="  Enter search term (e.g. dramatic piano, lofi guitar, epic sfx): "
    set music_target=%custom_query%
)

echo.
set /p music_limit="  Enter number of files to download [1]: "
if "%music_limit%"=="" set music_limit=1

"%PY%" main.py --download-music "%music_target%" --download-limit %music_limit% --download-folder "%music_folder%"
pause
goto MENU

:WEB_DASHBOARD
cls
echo ================================================================
echo             STARTING WEB CONTROL DASHBOARD
echo ================================================================
echo.
"%PY%" src/web/server.py
pause
goto MENU

:RUN_PUBLISHER
cls
echo ================================================================
echo             RUNNING AUTO-PUBLISHING PIPELINE
echo ================================================================
echo.
"%PY%" src/scripts/scheduler.py --force
pause
goto MENU
