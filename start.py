import os
import shutil
import configparser
import subprocess

def get_config(config_path='config.ini'):
    config = configparser.ConfigParser()
    config.read(config_path, encoding='utf-8')
    video_dir = config.get('settings', 'video_dir', fallback=None)
    ffmpeg_path = config.get('settings', 'ffmpeg_path', fallback='ffmpeg')
    return video_dir, ffmpeg_path

def copy_and_rename_m4s(directory):
    for root, _, files in os.walk(directory):
        if '1.m4s' in files and '2.m4s' in files:
            print(f"目录 {root} 已有 1.m4s 和 2.m4s，跳过。")
            continue

        m4s_files = [f for f in files if f.endswith('.m4s') and f not in ('1.m4s', '2.m4s')]
        m4s_files = sorted(m4s_files)[:2]

        if len(m4s_files) == 0:
            print(f"目录 {root} 没有找到可处理的 .m4s 文件，跳过。")
            continue

        for index, old_name in enumerate(m4s_files, start=1):
            old_path = os.path.join(root, old_name)
            new_name = f"{index}.m4s"
            new_path = os.path.join(root, new_name)

            if os.path.exists(new_path):
                os.remove(new_path)

            shutil.copy2(old_path, new_path)
            print(f"复制 {old_name} -> {new_name} 于目录 {root}")

def delete_first_9_bytes(directory):
    for root, _, files in os.walk(directory):
        for filename in files:
            if filename.endswith(('1.m4s', '2.m4s')) and 'delete8' not in filename:
                original_path = os.path.join(root, filename)
                new_filename = filename.replace('.m4s', '_delete8.m4s')
                new_path = os.path.join(root, new_filename)

                if os.path.exists(new_path):
                    print(f"跳过已存在的文件：{new_path}")
                    continue

                try:
                    shutil.copy2(original_path, new_path)
                    with open(new_path, 'r+b') as f:
                        content = f.read()
                        f.seek(0)
                        f.truncate()
                        f.write(content[9:])
                    print(f"成功复制并处理：{new_path}")
                except Exception as e:
                    print(f"处理文件时出错：{original_path}")
                    print(e)

def merge_m4s_to_mp4(base_dir, ffmpeg_path):
    for folder_name in os.listdir(base_dir):
        folder_path = os.path.join(base_dir, folder_name)
        if os.path.isdir(folder_path):
            m4s1 = os.path.join(folder_path, "1_delete8.m4s")
            m4s2 = os.path.join(folder_path, "2_delete8.m4s")
            output_file = os.path.join(folder_path, f"{folder_name}.mp4")

            if os.path.isfile(output_file):
                print(f"⚠️ 文件已存在，跳过合并：{output_file}")
                continue

            if os.path.isfile(m4s1) and os.path.isfile(m4s2):
                command = [
                    ffmpeg_path,
                    "-i", m4s1,
                    "-i", m4s2,
                    "-c", "copy",
                    output_file
                ]

                print(f"Merging: {folder_path}")
                result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

                if result.returncode == 0:
                    print(f"✅ 成功合并：{output_file}")
                else:
                    print(f"❌ 合并失败：{folder_path}\n{result.stderr}")
            else:
                print(f"⚠️ 缺少 1_delete8.m4s 或 2_delete8.m4s，{folder_path}")

if __name__ == "__main__":
    video_dir, ffmpeg_path = get_config()
    if video_dir and os.path.isdir(video_dir):
        copy_and_rename_m4s(video_dir)
        delete_first_9_bytes(video_dir)
        merge_m4s_to_mp4(video_dir, ffmpeg_path)
        print("✅ 所有处理完成。")
    else:
        print("❌ 未找到有效的 video_dir 或目录不存在。请检查 config.ini 配置。")
