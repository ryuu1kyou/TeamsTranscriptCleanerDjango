# Teams Transcript Cleaner - Django Enterprise Edition

堅牢で拡張性の高い Django フレームワークを使用した エンタープライズ向け Teams トランスクリプト処理システム

Microsoft Teams の会議録を AI で高精度に修正する本格的な Web アプリケーション

## 機能

- **誤字脱字修正**: カスタム辞書と AI を組み合わせた高精度な修正
- **文法修正**: 自然で読みやすい日本語への修正
- **要約生成**: 会議記録の重要ポイントを抽出した要約
- **ユーザー管理**: 個人用アカウントと API 使用量管理
- **ワードリスト管理**: 頻出する修正パターンの辞書管理
- **処理履歴**: 修正ジョブの履歴と結果管理

## Django の特徴

### 🏢 エンタープライズ対応

- 豊富な内蔵機能
- 高度なセキュリティ
- 大規模システムに最適

### 🛡️ 堅牢性

- 包括的な管理機能
- 高度な認証システム
- スケーラブルな設計

## システム要件

- Python 3.8+
- MySQL 5.7+ または 8.0+
- Redis (Celery 用、オプション)
- OpenAI API キー

## セットアップ手順

### 1. プロジェクトのクローンと環境構築

```bash
# プロジェクトディレクトリに移動
cd transcript-cleaner-django

# 仮想環境の作成
python -m venv venv

# 仮想環境の有効化 (Windows)
venv\Scripts\activate
# 仮想環境の有効化 (macOS/Linux)
source venv/bin/activate

# 依存パッケージのインストール
pip install -r requirements.txt
```

### 2. MySQL データベースの設定

#### MySQL サーバーへの接続

**Windows の場合:**

```bash
# MySQL Command Line Client を起動
mysql -u root -p
# または MySQL Workbench を使用
```

**macOS の場合:**

```bash
# Homebrew でインストールした場合
mysql -u root -p

# または MySQL Workbench を使用
```

**Linux (Ubuntu/Debian) の場合:**

```bash
# ターミナルから MySQL に接続
sudo mysql -u root -p
```

**Docker で MySQL を使用する場合:**

```bash
# MySQL 8.0 コンテナを起動
docker run --name mysql-transcript-db \
  -e MYSQL_ROOT_PASSWORD=rootpassword \
  -e MYSQL_DATABASE=transcript_cleaner_django \
  -d -p 3306:3306 mysql:8.0

# コンテナに接続してMySQL コマンドラインを起動
docker exec -it mysql-transcript-db mysql -u root -p
```

#### データベースとユーザーの作成

MySQL に root ユーザーでログイン後、以下のコマンドを順に実行：

```sql
-- 1. データベース作成（日本語対応）
CREATE DATABASE transcript_cleaner_django 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

-- 2. Django アプリケーション専用ユーザー作成
CREATE USER 'test'@'localhost' IDENTIFIED BY 'secure_password_123';

-- 3. 必要な権限をすべて付与
GRANT ALL PRIVILEGES ON transcript_cleaner_django.* TO 'test'@'localhost';

-- 4. 権限テーブルを再読み込み
FLUSH PRIVILEGES;

-- 5. 作成確認
SHOW DATABASES LIKE 'transcript_cleaner_django';
SELECT user, host FROM mysql.user WHERE user = 'test';

-- 6. データベースの文字セット確認
SELECT DEFAULT_CHARACTER_SET_NAME, DEFAULT_COLLATION_NAME 
FROM information_schema.SCHEMATA 
WHERE SCHEMA_NAME = 'transcript_cleaner_django';

-- 7. MySQL からログアウト
EXIT;
```

#### 接続テスト

作成したユーザーで正常に接続できるかテスト：

```bash
# Django ユーザーで接続テスト
mysql -u test -p transcript_cleaner_django
```

接続成功後、以下のコマンドで確認：

```sql
-- 現在のデータベース確認
SELECT DATABASE();

-- 権限確認
SHOW GRANTS FOR CURRENT_USER();

-- テーブル一覧（初期は空）
SHOW TABLES;

-- 文字セット確認
SHOW VARIABLES LIKE 'character_set%';

-- ログアウト
EXIT;
```

#### トラブルシューティング

**パスワード認証エラーの場合:**

```sql
-- MySQL 8.0 でパスワード認証方式を変更
ALTER USER 'test'@'localhost' IDENTIFIED WITH mysql_native_password BY 'secure_password_123';
FLUSH PRIVILEGES;
```

**権限エラーの場合:**

```sql
-- 権限を再確認・再付与
SHOW GRANTS FOR 'test'@'localhost';
GRANT ALL PRIVILEGES ON transcript_cleaner_django.* TO 'test'@'localhost';
FLUSH PRIVILEGES;
```

### 3. 環境変数の設定

`.env.example` を `.env` にコピーして設定：

```bash
cp .env.example .env
```

`.env` ファイルを編集し、以下の値を設定：

```env
SECRET_KEY=your-django-secret-key-here
DEBUG=True

# データベース設定
DB_NAME=transcript_cleaner_django
DB_USER=test
DB_PASSWORD=secure_password_123
DB_HOST=localhost
DB_PORT=3306

# OpenAI API 設定
OPENAI_API_KEY=your-openai-api-key-here

# Redis 設定 (Celery 用)
REDIS_URL=redis://localhost:6379/0

# ソーシャルログイン設定 (オプション)
# Google
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
# Microsoft
MICROSOFT_CLIENT_ID=your-microsoft-client-id
MICROSOFT_CLIENT_SECRET=your-microsoft-client-secret
```

### 4. ソーシャルログインの設定 (オプション)

本アプリケーションでは、Google および Microsoft アカウントを使用したソーシャルログインをサポートしています。設定は任意ですが、利用する場合は以下の手順に従ってください。

#### Google アカウントでのログイン設定

1.  **Google Cloud Console** にアクセスします。
2.  新しいプロジェクトを作成するか、既存のプロジェクトを選択します。
3.  **[API とサービス] > [認証情報]** に移動します。
4.  **[認証情報を作成] > [OAuth クライアント ID]** を選択します。
5.  アプリケーションの種類として **[ウェブ アプリケーション]** を選択します。
6.  **承認済みの JavaScript 生成元** に以下を追加します:
    - `http://127.0.0.1:8000`
    - `http://localhost:8000`
7.  **承認済みのリダイレクト URI** に以下を追加します:
    - `http://127.0.0.1:8000/accounts/google/login/callback/`
    - `http://localhost:8000/accounts/google/login/callback/`
8.  作成後、**クライアント ID** と **クライアントシークレット** をコピーし、`.env` ファイルに設定します。

#### Microsoft アカウントでのログイン設定

1.  **Azure Active Directory** の管理センターにアクセスします。
2.  **[アプリの登録] > [新規登録]** を選択します。
3.  アプリケーションに名前を付け、サポートされるアカウントの種類を選択します。
4.  **リダイレクト URI** に **[Web]** を選択し、以下を追加します:
    - `http://127.0.0.1:8000/accounts/microsoft/login/callback/`
    - `http://localhost:8000/accounts/microsoft/login/callback/`
5.  登録後、**アプリケーション (クライアント) ID** をコピーして `.env` ファイルに設定します。
6.  **[証明書とシークレット] > [新しいクライアント シークレット]** を作成し、その **値** をコピーして `.env` ファイルに設定します。

### 5. Django アプリケーションの初期化

```bash
# データベースマイグレーションの適用
# (ソーシャルアカウント機能のテーブルもここで作成されます)
python transcript_cleaner/manage.py migrate

# スーパーユーザーの作成
python transcript_cleaner/manage.py createsuperuser

# 静的ファイルの収集
python transcript_cleaner/manage.py collectstatic

# テストデータの作成 (開発環境のみ)
python transcript_cleaner/manage.py create_test_data
```

### 5. アプリケーションの起動

```bash
# 開発サーバーの起動
python transcript_cleaner/manage.py runserver

# ブラウザで http://127.0.0.1:8000/ にアクセス
```

## プロジェクト構造

```
django/
├── transcript_cleaner/           # メインプロジェクト
│   ├── config/                  # 設定ファイル
│   │   ├── settings/           # 環境別設定
│   │   ├── urls.py            # URL 設定
│   │   ├── wsgi.py            # WSGI 設定
│   │   └── asgi.py            # ASGI 設定
│   ├── apps/                   # Django アプリ
│   │   ├── accounts/          # ユーザー管理
│   │   ├── transcripts/       # トランスクリプト管理
│   │   ├── corrections/       # 修正ジョブ管理
│   │   ├── wordlists/         # ワードリスト管理
│   │   └── api/               # API エンドポイント
│   ├── templates/             # HTML テンプレート
│   ├── static/                # 静的ファイル
│   ├── media/                 # アップロードファイル
│   └── manage.py              # Django 管理コマンド
├── processing/                 # 処理ロジック
│   ├── openai_service.py      # OpenAI API 統合
│   └── csv_parser.py          # CSV パーサー
├── requirements.txt           # Python 依存関係
├── .env.example              # 環境変数テンプレート
└── README.md                 # このファイル
```

## 主要機能の使用方法

### 1. 初回ログイン

1. ブラウザで `http://127.0.0.1:8000/` にアクセス
2. テストアカウントでログイン:
   - **管理者**: `admin@example.com` / `admin123`
   - **一般ユーザー**: `test@example.com` / `test123`

### 2. 訂正処理の実行手順

#### ステップ1: ファイルアップロード
1. 左サイドバーの「ファイルアップロード」セクション
2. 「訂正前議事録（TXT）」でTeamsの会議録ファイルを選択
3. ファイル情報（文字数、推定コスト）が表示される

#### ステップ2: 処理モード選択
- **誤字脱字修正**: CSVワードリストを使用した厳密な修正
- **文法修正**: 自然な日本語への修正
- **要約**: 会議内容の要約生成

#### ステップ3: ワードリスト設定（誤字脱字修正の場合）
CSVエディタで修正パターンを入力：
```csv
誤,正
マイクロソフト,Microsoft
エクセル,Excel
```

#### ステップ4: 処理実行
1. 「訂正実行」ボタンをクリック
2. 処理完了まで待機（通常数秒〜1分）
3. 右側エリアに結果が表示される

#### ステップ5: 結果確認と保存
1. 「差分表示」で修正内容を確認
2. 必要に応じて手動修正を行う
3. 「最終確定ダウンロード」でファイル保存

### 3. コスト管理

- **現在のセッション**: セッション中の累積コスト
- **累計使用コスト**: アカウント全体の使用量
- **残り予算**: 使用可能な残り予算
- 使用制限に達すると処理が制限される

### 4. その他の便利機能

- **コピー機能**: 修正結果を再度の修正用に訂正前エリアにコピー
- **差分表示**: 修正前後の変更点をハイライト表示
- **モデル選択**: GPT-4o、GPT-4 Turbo等から選択可能

## API エンドポイント

### 認証

- `POST /api/v1/auth/login/` - ログイン
- `POST /api/v1/auth/logout/` - ログアウト
- `POST /api/v1/auth/register/` - ユーザー登録

### トランスクリプト

- `GET /api/v1/transcripts/` - トランスクリプト一覧
- `POST /api/v1/transcripts/` - 新規作成
- `GET /api/v1/transcripts/{id}/` - 詳細取得

### 修正ジョブ

- `GET /api/v1/corrections/` - ジョブ一覧
- `POST /api/v1/corrections/` - 修正実行
- `GET /api/v1/corrections/{id}/` - ジョブ詳細

### ワードリスト

- `GET /api/v1/wordlists/` - ワードリスト一覧
- `POST /api/v1/wordlists/` - 新規作成
- `GET /api/v1/wordlists/{id}/` - 詳細取得

## 開発・デバッグ

### テストデータの作成

```bash
python transcript_cleaner/manage.py create_test_data
```

作成されるテストアカウント：

- 管理者: `admin@example.com` / `admin123`
- 一般ユーザー: `test@example.com` / `test123`

### ログの確認

Django ログは標準出力に表示されます。本格運用時は `settings/production.py` でログ設定を調整してください。

### デバッグツール

開発環境では Django Debug Toolbar が有効になっています。

## 本番環境での運用

### 1. 環境設定

```bash
# 本番環境用設定の使用
export DJANGO_SETTINGS_MODULE=config.settings.production

# DEBUG を無効化
export DEBUG=False

# セキュリティ設定
export SECRET_KEY=your-production-secret-key
export ALLOWED_HOSTS=your-domain.com
```

### 2. Web サーバー設定

Gunicorn + Nginx での運用例：

```bash
# Gunicorn の起動
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

### 3. 静的ファイルの配信

```bash
python transcript_cleaner/manage.py collectstatic --noinput
```

### 4. データベースバックアップ

```bash
# MySQL バックアップ
mysqldump -u test -p transcript_cleaner_django > backup.sql

# Django のフィクスチャとしてエクスポート
python transcript_cleaner/manage.py dumpdata > backup.json
```

## よくある問題と解決方法

### 1. 500エラーが発生する場合

#### OpenAI API関連のエラー
```
Client.__init__() got an unexpected keyword argument 'proxies'
```
**解決方法**: OpenAIライブラリを最新版に更新
```bash
pip install openai==1.95.1
```

#### データ型変換エラー
**症状**: JSON応答でコストが文字列として表示される  
**解決方法**: すでに修正済み（Decimal→float変換の実装）

### 2. JavaScript エラーが発生する場合

#### 変数重複宣言エラー
```
Identifier 'sessionCost' has already been declared
```
**解決方法**: ブラウザキャッシュをクリア
- **Windows**: `Ctrl+Shift+R`
- **Mac**: `Cmd+Shift+R`
- または開発者ツール → Network → "Disable cache"にチェック

### 3. データベース接続エラー

1. **MySQL 接続エラー**
   - `.env` ファイルのデータベース設定を確認
   - MySQL サービスが起動しているか確認
   ```bash
   # Windows
   net start mysql80
   
   # Linux/Mac
   sudo systemctl start mysql
   ```

2. **認証エラー**
   ```sql
   -- MySQL 8.0で認証方式を変更
   ALTER USER 'test'@'localhost' IDENTIFIED WITH mysql_native_password BY 'secure_password_123';
   FLUSH PRIVILEGES;
   ```

### 4. OpenAI API エラー

1. **API キーが無効**
   - `.env`ファイルの`OPENAI_API_KEY`を確認
   - OpenAI ダッシュボードでキーが有効か確認

2. **使用量制限エラー**
   - OpenAI アカウントの使用量制限を確認
   - 課金設定が正しく設定されているか確認

### 5. 静的ファイルが表示されない

```bash
# 静的ファイルを再収集
python transcript_cleaner/manage.py collectstatic

# 開発サーバーの再起動
python transcript_cleaner/manage.py runserver
```

### デバッグのコツ

#### 開発者ツールの活用
1. **F12** でブラウザ開発者ツールを開く
2. **Console** タブでJavaScriptエラーを確認
3. **Network** タブでAPI通信の状態を確認
4. **Application** タブでローカルストレージやキャッシュを確認

#### Django デバッグ情報
開発環境では詳細なエラー情報が表示されます。本番環境では`DEBUG=False`に設定してください。

### ログ確認

```bash
# Django ログ
tail -f django.log

# MySQL エラーログ (Linux/Mac)
tail -f /var/log/mysql/error.log

# Windows MySQL ログ
# C:\ProgramData\MySQL\MySQL Server 8.0\Data\*.err
```

## ログイン機能について

### 実装されている認証機能

✅ **ユーザー登録**

- メールアドレスとパスワードによる新規登録
- 組織名の設定（任意）
- 自動プロフィール作成

✅ **ログイン・ログアウト**

- メールアドレスまたはユーザー名でログイン
- セッション管理
- 安全なログアウト

✅ **アクセス制御**

- ログイン必須ページの保護
- ユーザー別データ分離
- API使用量管理

✅ **テストアカウント**
開発・テスト用のアカウントが自動作成されます：

- **管理者**: `admin@example.com` / `admin123`
- **一般ユーザー**: `test@example.com` / `test123`

### セキュリティ機能

- Django標準の認証システム
- CSRF保護
- パスワード強度チェック
- セッションハイジャック対策
