"""
Management command to create test data for development.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.accounts.models import UserProfile
from apps.transcripts.models import TranscriptDocument
from apps.wordlists.models import WordList
from decimal import Decimal

User = get_user_model()


class Command(BaseCommand):
    help = 'Create test data for development'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing test data before creating new data',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing test data...')
            User.objects.filter(email__endswith='@example.com').delete()

        # Create test users
        self.stdout.write('Creating test users...')
        
        # Admin user
        admin_user, created = User.objects.get_or_create(
            email='admin@example.com',
            defaults={
                'username': 'admin',
                'first_name': 'Admin',
                'last_name': 'User',
                'is_staff': True,
                'is_superuser': True,
                'api_usage_limit': Decimal('50.00')
            }
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            UserProfile.objects.create(user=admin_user)
            self.stdout.write(f'Created admin user: {admin_user.email}')

        # Regular test user
        test_user, created = User.objects.get_or_create(
            email='test@example.com',
            defaults={
                'username': 'testuser',
                'first_name': 'Test',
                'last_name': 'User',
                'organization': 'Test Company',
                'api_usage_limit': Decimal('10.00')
            }
        )
        if created:
            test_user.set_password('test123')
            test_user.save()
            UserProfile.objects.create(user=test_user)
            self.stdout.write(f'Created test user: {test_user.email}')

        # Create test transcript
        sample_content = """
Teams 会議議事録

参加者：
- 田中さん（プロジェクトマネージャー）
- 佐藤さん（エンジニア）
- 鈴木さん（デザイナー）

議題：
1. プロジェクトの進捗確認
2. 次週のタスク分担
3. 問題点の洗い出し

内容：
田中：皆さん、今日はお疲れ様です。まず、今週の進捗を確認しましょう。
佐藤：フロントエンドの実装は80%程度完了しています。ただ、一部のコンポーネントでエラーが発生しています。
鈴木：デザインは全て完了しました。修正依頼があれば対応します。
田中：ありがとうございます。来週までに残りのタスクを完了させましょう。
"""

        transcript, created = TranscriptDocument.objects.get_or_create(
            user=test_user,
            title='サンプル会議議事録',
            defaults={
                'original_filename': 'sample_meeting.txt',
                'content': sample_content.strip(),
                'file_size': len(sample_content.strip().encode('utf-8'))
            }
        )
        if created:
            self.stdout.write(f'Created test transcript: {transcript.title}')

        # Create test word list
        csv_content = """誤,正
田中,田中
佐藤,佐藤
鈴木,鈴木
フロントエンド,フロントエンド
コンポーネント,コンポーネント
エラー,エラー
タスク,タスク"""

        wordlist, created = WordList.objects.get_or_create(
            user=test_user,
            name='サンプル修正リスト',
            defaults={
                'description': 'テスト用の修正リスト',
                'csv_content': csv_content,
                'is_active': True
            }
        )
        if created:
            self.stdout.write(f'Created test word list: {wordlist.name}')

        self.stdout.write(
            self.style.SUCCESS('Successfully created test data!')
        )
        self.stdout.write('Test accounts:')
        self.stdout.write('  Admin: admin@example.com / admin123')
        self.stdout.write('  User:  test@example.com / test123')