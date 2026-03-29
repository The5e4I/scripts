@echo off
setlocal enabledelayedexpansion

for %%F in (*.mp3) do (
    set "filename=%%~nF"

    REM Extract track number and title
    for /f "tokens=1*" %%A in ("!filename!") do (
        set "track=%%A"
        set "title=%%B"

        echo タグ付け中: Track=!track! Title=!title!

        ffmpeg -i "%%F" -y -metadata title="!title!" -metadata track="!track!" -codec copy "temp_%%F"
        move /Y "temp_%%F" "%%F" >nul
    )
)

echo 全てのMP3にタグを付けました。
pause
