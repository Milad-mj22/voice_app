"""
جمع‌آوری کد پروژه — به تفکیک پوشه
"""
import os
from pathlib import Path

# ═══════════════ تنظیمات ═══════════════
OUTPUT_FILE = "project_code.txt"
INCLUDE_EXTENSIONS = {".py", ".html", ".js", ".css"}
EXCLUDE_DIRS = {
    "venv", "myenv", "env", ".venv",
    "__pycache__", ".git", ".idea", ".vscode",
    "node_modules", "staticfiles", "media",
}
EXCLUDE_FILES = {
    "collect_code.py",
    OUTPUT_FILE,
    "db.sqlite3",
}
# ════════════════════════════════════════


def should_exclude_dir(dirname):
    return dirname in EXCLUDE_DIRS or dirname.startswith(".")


def find_files(root):
    results = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if not should_exclude_dir(d)]

        for f in filenames:
            if f in EXCLUDE_FILES:
                continue
            if Path(f).suffix.lower() in INCLUDE_EXTENSIONS:
                full = os.path.join(dirpath, f)
                rel = os.path.relpath(full, root)
                results.append(rel)

    return sorted(results)


def group_by_folder(files):
    """فایل‌ها رو بر اساس پوشه‌ی بلافصل گروه‌بندی کن"""
    groups = {}
    for rel in files:
        folder = os.path.dirname(rel) or "."    # فایل‌های ریشه
        groups.setdefault(folder, []).append(rel)
    return groups


def ask_folders(groups):
    """از کاربر برای هر پوشه بپرس"""
    print(f"\n🔍 {len(groups)} پوشه پیدا شد.\n")
    print("برای هر پوشه یکی از گزینه‌ها رو بزن:")
    print("  y = اضافه کن")
    print("  n = رد کن")
    print("  a = همه‌ی بعدی‌ها رو اضافه کن")
    print("  q = خروج")
    print("  (Enter = اضافه کن)\n")

    selected_folders = []
    add_all = False

    folders_sorted = sorted(groups.keys())

    for i, folder in enumerate(folders_sorted, 1):
        count = len(groups[folder])

        if add_all:
            selected_folders.append(folder)
            print(f"  ✅ [{i}/{len(folders_sorted)}] {folder}  ({count} فایل)")
            continue

        while True:
            try:
                ans = input(f"[{i}/{len(folders_sorted)}] 📁 {folder}  ({count} فایل) ? (y/n/a/q) ").strip().lower()
            except KeyboardInterrupt:
                print("\nخروج...")
                return selected_folders

            if ans == "" or ans == "y":
                selected_folders.append(folder)
                break
            elif ans == "n":
                break
            elif ans == "a":
                add_all = True
                selected_folders.append(folder)
                print("  ⚡ همه‌ی بعدی‌ها اضافه می‌شن.")
                break
            elif ans == "q":
                print("\nخروج...")
                return selected_folders
            else:
                print("  ❓ لطفاً y/n/a/q بزن.")

    return selected_folders


def collect(root, files):
    output_path = os.path.join(root, OUTPUT_FILE)

    total_lines = 0

    with open(output_path, "w", encoding="utf-8") as out:
        out.write("=" * 70 + "\n")
        out.write("گزارش کد پروژه\n")
        out.write(f"تعداد فایل‌ها: {len(files)}\n")
        out.write("=" * 70 + "\n\n")

        for i, rel in enumerate(files, 1):
            full = os.path.join(root, rel)
            try:
                with open(full, "r", encoding="utf-8") as f:
                    content = f.read()
            except UnicodeDecodeError:
                try:
                    with open(full, "r", encoding="latin-1") as f:
                        content = f.read()
                except Exception as e:
                    content = f"[خطا: {e}]"
            except Exception as e:
                content = f"[خطا: {e}]"

            lines = content.count("\n") + 1
            total_lines += lines

            out.write("\n" + "=" * 70 + "\n")
            out.write(f"📄 فایل {i}/{len(files)}: {rel}\n")
            out.write(f"📏 {lines} خط\n")
            out.write("=" * 70 + "\n\n")
            out.write(content)
            out.write("\n\n")

        out.write("\n" + "=" * 70 + "\n")
        out.write(f"جمع کل: {len(files)} فایل — {total_lines} خط\n")
        out.write("=" * 70 + "\n")

    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"\n✅ فایل ساخته شد: {output_path}")
    print(f"📦 حجم: {size_mb:.2f} MB")
    print(f"📄 تعداد فایل: {len(files)}")
    print(f"📏 مجموع خطوط: {total_lines}")


def main():
    root = os.path.dirname(os.path.abspath(__file__))
    print(f"📂 پوشه‌ی پروژه: {root}")

    print("\n🔍 در حال جستجو...")
    files = find_files(root)

    if not files:
        print("❌ هیچ فایلی پیدا نشد.")
        return

    groups = group_by_folder(files)

    selected_folders = ask_folders(groups)

    if not selected_folders:
        print("\n⚠️ هیچ پوشه‌ای انتخاب نشد. خروج.")
        return

    # فایل‌های انتخاب‌شده رو جمع کن
    selected_files = []
    for folder in selected_folders:
        selected_files.extend(groups[folder])

    # مرتب‌سازی بر اساس مسیر
    selected_files.sort()

    print(f"\n📝 در حال نوشتن {len(selected_files)} فایل از {len(selected_folders)} پوشه...")
    collect(root, selected_files)


if __name__ == "__main__":
    main()