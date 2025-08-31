# Teams Transcript Cleaner - Django Enterprise Edition Technical Documentation

Django Enterprise Edition は堅牢性と拡張性を重視したエンタープライズ向けトランスクリプト処理システムです。

このドキュメントは、Claude AI によって設計・開発された Django Enterprise Edition の技術詳細とアーキテクチャを記録します。

## 開発概要

### プロジェクト背景
- **開発目的**: 大規模運用に対応する堅牢な Django ベースのトランスクリプト処理システム
- **設計思想**: エンタープライズレベルの信頼性とスケーラビリティ
- **開発期間**: 2025年7月〜8月
- **開発者**: Claude AI (Anthropic)
- **最新更新**: 2025年8月31日 - Django国際化対応完了

### アーキテクチャ設計思想

#### 1. モジュラー設計
```
transcript-cleaner-django/
├── transcript_cleaner/           # Django プロジェクト
│   ├── apps/                    # 機能別アプリケーション
│   │   ├── accounts/           # ユーザー管理
│   │   ├── transcripts/        # トランスクリプト管理
│   │   ├── corrections/        # 修正処理
│   │   ├── wordlists/          # 辞書管理
│   │   └── api/                # REST API
│   └── config/                 # 設定管理
└── processing/                  # ビジネスロジック
```

#### 2. 責任分離の原則
- **Views**: リクエスト処理とレスポンス生成
- **Models**: データ構造とビジネスルール
- **Processing**: OpenAI API 統合とテキスト処理
- **Templates**: ユーザーインターフェース

#### 3. セキュリティ設計
- Django 標準の認証システム
- CSRF 保護
- API キー管理
- ユーザー別リソース分離

## 技術仕様

### データベース設計

#### User Model (カスタムユーザー)
```python
class User(AbstractUser):
    email = models.EmailField(unique=True)
    organization = models.CharField(max_length=100)
    api_usage_limit = models.DecimalField(max_digits=10, decimal_places=2)
    total_api_cost = models.DecimalField(max_digits=10, decimal_places=4)
    is_verified = models.BooleanField(default=False)
```

#### TranscriptDocument Model
```python
class TranscriptDocument(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    content = models.TextField()
    file_size = models.PositiveIntegerField()
    character_count = models.PositiveIntegerField()
    word_count = models.PositiveIntegerField()
    is_processed = models.BooleanField(default=False)
```

#### CorrectionJob Model
```python
class CorrectionJob(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    PROCESSING_MODE_CHOICES = [
        ('proofreading', 'Proofreading'),
        ('grammar', 'Grammar Correction'),
        ('summary', 'Summary Generation'),
        ('custom', 'Custom Processing'),
    ]
```

#### WordList Model
```python
class WordList(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    csv_content = models.TextField()
    word_count = models.PositiveIntegerField()
    is_shared = models.BooleanField(default=False)
```

### API 設計

#### RESTful エンドポイント
```
POST /api/v1/auth/login/           # ユーザーログイン
POST /api/v1/auth/register/        # ユーザー登録
GET  /api/v1/transcripts/          # トランスクリプト一覧
POST /api/v1/transcripts/          # 新規トランスクリプト作成
POST /api/v1/corrections/          # 修正ジョブ実行
GET  /api/v1/wordlists/            # ワードリスト一覧
```

#### 認証システム
- Django Session Authentication (Web UI)
- JWT Authentication (API)
- User permission-based access control

### OpenAI API 統合

#### モデル対応
```python
MODEL_PRICING = {
    "gpt-4o": 0.01,
    "gpt-4o-mini": 0.005,
    "gpt-4-turbo": 0.01,
    "gpt-4": 0.03,
    "gpt-3.5-turbo": 0.0015,
}
```

#### 処理モード
1. **Proofreading (誤字脱字修正)**
   - ワードリストベースの厳密な修正
   - 文章構造の保持

2. **Grammar (文法修正)**
   - 自然な日本語への修正
   - 表現の改善

3. **Summary (要約)**
   - 重要ポイントの抽出
   - 簡潔な要約生成

#### コスト管理
- ユーザー別API使用量追跡
- リアルタイムコスト計算
- 使用制限とアラート

### UI/UX 設計

#### フロントエンド技術
- **Bootstrap 5**: レスポンシブデザイン
- **Font Awesome**: アイコンライブラリ
- **JavaScript**: インタラクティブ機能

#### 主要画面
1. **ダッシュボード**: 利用状況とクイックアクション
2. **処理実行画面**: 設定とプレビュー
3. **結果表示**: 差分表示と編集機能
4. **管理画面**: Django Admin による管理

### セキュリティ機能

#### データ保護
- ユーザー別データ分離
- ファイルアップロード検証
- SQLインジェクション対策

#### API セキュリティ
- レート制限
- 入力値検証
- エラーハンドリング

## 開発プロセス

### 段階的実装

#### Phase 1: 基盤構築
1. Django プロジェクト構造設計
2. モデル設計と実装
3. 認証システム実装

#### Phase 2: コア機能
1. トランスクリプト管理
2. ワードリスト機能
3. OpenAI API 統合

#### Phase 3: UI/UX
1. Web インターフェース
2. 管理画面
3. レスポンシブデザイン

#### Phase 4: 国際化対応 (2025年8月実装)
1. Django i18n システム実装
2. 日本語・英語の多言語対応
3. Google OAuth の多言語URL対応
4. 動的言語切り替え機能

#### Phase 5: 最適化
1. パフォーマンス改善
2. エラーハンドリング
3. テストケース

### 品質管理

#### コード品質
- Django ベストプラクティス準拠
- PEP 8 スタイルガイド
- 型ヒント使用

#### セキュリティ
- Django セキュリティチェックリスト
- 脆弱性スキャン
- セキュアコーディング

#### テスト戦略
- ユニットテスト
- 統合テスト
- エンドツーエンドテスト

## 設定とデプロイ

### 環境設定

#### 必要な環境変数
```bash
SECRET_KEY=django-secret-key
DEBUG=True/False
DB_NAME=transcript_cleaner
DB_USER=database_user
DB_PASSWORD=database_password
DB_HOST=localhost
DB_PORT=3306
OPENAI_API_KEY=openai-api-key
REDIS_URL=redis://localhost:6379/0
```

#### データベース設定
- **開発**: SQLite (デフォルト)
- **本番**: MySQL 8.0+ 推奨
- **キャッシュ**: Redis (Celery用)

### デプロイメント

#### 本番環境推奨構成
```
Load Balancer (Nginx)
    ↓
Web Server (Gunicorn)
    ↓
Django Application
    ↓
Database (MySQL)
Cache (Redis)
```

#### パフォーマンス最適化
- 静的ファイル配信 (Nginx)
- データベース接続プーリング
- キャッシュ戦略
- 非同期処理 (Celery)

## 運用とメンテナンス

### ログ管理
- アプリケーションログ
- エラーログ
- API アクセスログ
- セキュリティログ

### モニタリング
- システムメトリクス
- パフォーマンス監視
- エラー追跡
- ユーザー行動分析

### バックアップ戦略
- データベースバックアップ
- ユーザーファイルバックアップ
- 設定ファイルバックアップ
- 災害復旧計画

## 最新アップデート (2025年8月)

### UI/UX 大幅改善
1. **ユーザー管理機能の実装**
   - 管理画面にタブスタイルのユーザー管理・ロール管理を追加
   - Django Groups モデルと連携したロールベース権限管理
   - ユーザー一覧、編集、削除機能
   - リサイズ可能な3/4幅サイドバー

2. **多言語対応の完全実装**
   - Django Internationalization (i18n) への移行
   - URL多言語化 (`/en/`, `/ja/`)
   - サーバーサイドでの翻訳処理
   - SEO最適化対応

3. **ログインページのリデザイン**
   - 独立したHTMLテンプレートに変更
   - 適切なGoogleログインボタンサイズ調整
   - 一貫したボタン幅デザイン
   - 言語選択機能の底部配置

### 技術的改善
1. **フロントエンド最適化**
   - JavaScriptキャッシュ問題の解決
   - タブインターフェースの実装
   - レスポンシブサイドバーデザイン

2. **国際化設定**
   ```python
   # settings/base.py
   MIDDLEWARE = [
       # ...
       'django.middleware.locale.LocaleMiddleware',
       # ...
   ]
   
   LANGUAGES = [
       ('ja', 'Japanese'),
       ('en', 'English'),
   ]
   ```

3. **URL構造の改善**
   ```python
   # urls.py
   urlpatterns += i18n_patterns(
       path('accounts/', include('apps.accounts.urls')),
       path('transcripts/', include('apps.transcripts.urls')),
       prefix_default_language=False,
   )
   ```

### 最新バグ修正・機能改善 (2025年8月31日)

1. **JavaScript エラー修正**
   - `getCurrentRoles` 関数未定義エラーの解決
   - ロール編集機能の正常動作確保
   ```javascript
   // 追加された getCurrentRoles 関数
   async function getCurrentRoles() {
       const response = await fetch('/accounts/api/roles/', {
           method: 'GET',
           headers: {
               'X-CSRFToken': getCSRFToken(),
               'Content-Type': 'application/json',
           },
           credentials: 'same-origin'
       });
       if (response.ok) {
           const data = await response.json();
           return data.roles || [];
       }
       return [];
   }
   ```

2. **UI改善とブランディング**
   - 左サイドバーのボタンラベル変更: "ユーザー管理" → "管理"
   - より簡潔で直感的なラベリング
   - 多言語対応: "User Management" → "Management"

3. **翻訳ファイル更新**
   - 日本語翻訳ファイル (`locale/ja/LC_MESSAGES/django.po`) 更新
   - 英語翻訳ファイル (`locale/en/LC_MESSAGES/django.po`) 更新
   - 翻訳コンパイル実行で即座に反映

4. **プロジェクト整理**
   - 不要ファイル・ディレクトリ削除:
     - `sample/` (古いStreamlitアプリ)
     - `.superdesign/` (デザイン作業ファイル)
     - `.cursor/`, `.spec/` (開発ツール固有ファイル)
     - `check_independence.py`, `setup.py`, `SETUP_COMPLETE.md`
     - `仕様駆動開発.md` (重複仕様書)
   - `.gitignore` 強化でクリーンな状態維持
   - git履歴から削除済みテンプレートファイル除去

## 今後の拡張計画

### 機能拡張
1. **✅ 多言語対応**: 日本語・英語対応完了
2. **リアルタイム処理**: WebSocket 統合
3. **共同編集**: 複数ユーザーでの同時編集
4. **AI モデル選択**: 他の AI サービス統合
5. **ロール管理システム**: Django Groups完全統合

### アーキテクチャ改善
1. **マイクロサービス化**: 機能別サービス分離
2. **イベント駆動**: 非同期メッセージング
3. **API Gateway**: 統一されたAPI管理
4. **コンテナ化**: Docker/Kubernetes対応

### 性能向上
1. **キャッシュ最適化**: Redis Cluster
2. **データベース最適化**: 読み書き分離
3. **CDN 統合**: グローバル配信
4. **負荷分散**: オートスケーリング

## トラブルシューティング

### 開発中に遭遇した主要な問題と解決方法

#### 1. OpenAI ライブラリ互換性エラー
- **症状**: `Client.__init__() got an unexpected keyword argument 'proxies'`
- **原因**: OpenAI ライブラリのバージョン不一致（v1.7.2 → v1.95.1）
- **解決**: `pip install openai==1.95.1` でライブラリ更新

#### 2. Decimal/Float 型変換エラー
- **症状**: JSON シリアライゼーション時に Decimal が文字列として出力される
- **原因**: Python Decimal と OpenAI API の float 戻り値の型ミスマッチ
- **解決**: 
  ```python
  # processing/openai_service.py 内で float() に変換
  cost = float((total_tokens / 1000) * price_per_1k)
  
  # API endpoint で明示的な型変換
  current_cost = float(request.user.total_api_cost)
  usage_limit = float(request.user.api_usage_limit)
  ```

#### 3. JavaScript キャッシュ問題
- **症状**: `Identifier 'sessionCost' has already been declared` エラー
- **原因**: ブラウザキャッシュによる古いJavaScriptファイル読み込み
- **解決**: 
  - ハードリフレッシュ (Ctrl+Shift+R / Cmd+Shift+R)
  - JSファイルにバージョンパラメータ追加: `workspace.js?v=2`
  - ブラウザ開発者ツールで「Disable cache」有効化

#### 4. データベースマイグレーション競合
- **症状**: マイグレーションファイルの競合やカスタムユーザーモデル関連エラー
- **原因**: カスタムUser モデルの設定と Django 内蔵アプリの初期化順序
- **解決**: 
  - `INSTALLED_APPS` の順序調整
  - カスタム User モデルを最初にマイグレーション
  - 依存関係の明示的定義

#### 5. CSRF トークンエラー
- **症状**: POST リクエストで 403 Forbidden エラー
- **原因**: JavaScript での CSRF トークン取得失敗
- **解決**: 
  ```javascript
  function getCSRFToken() {
      const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
      return csrfToken ? csrfToken.value : '';
  }
  ```

#### 6. ログインページの巨大Googleロゴ問題
- **症状**: login_ng.pngのように巨大なGoogleロゴが表示される
- **原因**: `{% extends 'base.html' %}` でbase.htmlの影響を受けている
- **解決**: ログインテンプレートを独立したHTMLドキュメントに変更し、適切なCSSサイジングを適用

#### 7. 多言語切り替えの不完全性
- **症状**: 英語モードでも一部日本語テキストが表示される、英語に切り替えても日本語に戻ってしまう
- **原因**: JavaScriptベースの翻訳による一時的な日本語表示、メインワークスペース画面のi18n未対応
- **解決**: Django Internationalization (i18n) に移行
  - `LocaleMiddleware` を追加
  - `i18n_patterns` でURL多言語化
  - `{% trans %}` タグで翻訳対応
  - メインワークスペース画面のJavaScript翻訳をDjango i18nに統合

### JavaScript デバッグのベストプラクティス

#### ブラウザキャッシュ対策
1. **開発時の設定**:
   - 開発者ツール → Network → Disable cache
   - プライベートブラウザモードでの動作確認

2. **本番対策**:
   - 静的ファイルにバージョニング
   - `{% static 'js/workspace.js' %}?v=2`

3. **キャッシュクリア手順**:
   - Windows: `Ctrl+Shift+R`
   - Mac: `Cmd+Shift+R`
   - または設定 → プライバシー → 閲覧データの削除

### API エンドポイント開発の注意点

#### 型変換の一貫性
```python
# 悪い例: 型が混在
current_cost = request.user.total_api_cost  # Decimal
estimated_cost = 0.0001  # float

# 良い例: 明示的な型変換
current_cost = float(request.user.total_api_cost)  # float
estimated_cost = float(estimated_cost)  # float
```

#### エラーハンドリング
```python
# 本番環境では console.error や詳細なトレースバックを避ける
try:
    result = some_operation()
    return JsonResponse({'success': True, 'data': result})
except Exception as e:
    # 本番: 簡潔なエラーメッセージ
    return JsonResponse({'error': 'Processing failed'}, status=500)
    # 開発: 詳細なエラー情報（デバッグ時のみ）
    # return JsonResponse({'error': str(e), 'traceback': traceback.format_exc()})
```

### よくある問題

#### 1. OpenAI API エラー
- **症状**: API 呼び出し失敗
- **原因**: API キー無効、レート制限、ライブラリバージョン不一致
- **解決**: キー確認、ライブラリ更新、リトライ機構

#### 2. データベース接続エラー
- **症状**: 500 Internal Server Error
- **原因**: DB 設定、接続数制限
- **解決**: 接続設定確認、プール調整

#### 3. ファイルアップロードエラー
- **症状**: ファイル処理失敗
- **原因**: サイズ制限、形式不正
- **解決**: バリデーション強化

### デバッグツール
- Django Debug Toolbar
- Django Extensions
- ブラウザ開発者ツール
- ログ分析ツール
- パフォーマンスプロファイラ

## 開発者向け情報

### 開発環境セットアップ
```bash
# 仮想環境作成
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 依存関係インストール
pip install -r requirements.txt

# データベース初期化
python manage.py migrate

# テストデータ作成
python manage.py create_test_data

# 開発サーバー起動
python manage.py runserver
```

### 開発ガイドライン
1. **PEP 8** コーディング規約準拠
2. **型ヒント** の積極的使用
3. **ドキュメンテーション** の充実
4. **テストファースト** 開発

### コントリビューション
- Issue 作成前の既存確認
- プルリクエスト前のテスト実行
- コードレビュー参加
- ドキュメント更新

---

**作成者**: Claude AI (Anthropic)  
**最終更新**: 2025年8月31日  
**バージョン**: 2.0.0

### 主要アップデート履歴
- **v2.0.0** (2025/08/31): ユーザー管理、多言語対応、UI/UX大幅改善
- **v1.0.0** (2025/07): 初回リリース、基本機能実装

