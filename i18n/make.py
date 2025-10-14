#!/usr/bin/env python3
"""
DV-Helper Translation Management Tool

This Python script providing cross-platform functionality for
managing translations in the DV-Helper project.

Usage:
  python maken.py [command]

Commands:
  1 or update     Update all existing translations
  2 or create [lang] Initialize a new translation (e.g. 'zh_CN')
  3 or compile    Compile all translation files
  Without arguments: Show interactive menu
"""

import sys
import subprocess
from pathlib import Path
import glob


class TranslationManager:
	def __init__(self):
		self.domain = 'dvhelper'
		self.i18n_dir = Path(__file__).parent.resolve()
		self.root_dir = self.i18n_dir.parent.resolve()
		self.pot_file = self.i18n_dir / f'{self.domain}.pot'
		self.babel_config = self.i18n_dir / 'babel.config'

	def run_command(self, cmd: list):
		"""Run a command using subprocess, handling errors appropriately"""
		try:
			print(f'Running: {" ".join(cmd)}')
			subprocess.run(cmd, check=True)
		except subprocess.CalledProcessError as e:
			print(f'Error executing command: {e}')
			sys.exit(1)

	def extract_messages(self):
		"""Extract translation messages from source code"""
		print('Extracting translation messages...')
		cmd = [
			'poetry', 'run', 'pybabel', 'extract',
			str(self.root_dir),
			'-F', str(self.babel_config),
			'-o', str(self.pot_file),
			'--no-location',
			'--omit-header'
		]
		self.run_command(cmd)

	def update_translations(self):
		"""Update all existing translation files"""
		# Check if there are any .po files
		po_files = glob.glob(str(self.i18n_dir / '**' / '*.po'), recursive=True)

		if not po_files:
			print('No existing message catalogs found.')
			print('Please use "create" command to initialize a new translation.')
			return

		# Extract messages first
		self.extract_messages()

		print('Updating translations...')
		cmd = [
			'poetry', 'run', 'pybabel', 'update',
			'-D', self.domain,
			'-i', str(self.pot_file),
			'-d', str(self.i18n_dir),
			'--omit-header'
		]
		self.run_command(cmd)

	def create_translation(self, lang: str=None):
		"""Create a new translation for the specified language"""
		# If language code is not provided, prompt user
		if not lang:
			lang = input('Enter language code (format: zh_CN): ').strip()

		if not lang:
			print('Error: Language code cannot be empty.')
			sys.exit(1)

		# Check if message catalog already exists
		po_file = self.i18n_dir / lang / 'LC_MESSAGES' / f'{self.domain}.po'
		po_file_rel = str(po_file.relative_to(self.i18n_dir))

		if po_file.exists():
			print(f'Error: Message catalog {po_file_rel} already exists.')
			print('Please use "update" command to update existing translations.')
			sys.exit(1)

		# Extract messages first
		self.extract_messages()

		# Initialize new translation
		print(f'Initializing {lang} translation...')
		cmd = [
			'poetry', 'run', 'pybabel', 'init',
			'-D', self.domain,
			'-i', str(self.pot_file),
			'-d', str(self.i18n_dir),
			'-l', lang
		]
		self.run_command(cmd)

	def compile_translations(self):
		"""Compile all translation files into binary format"""
		print('Compiling translation files...')
		cmd = [
			'poetry', 'run', 'pybabel', 'compile',
			'-D', self.domain,
			'-d', str(self.i18n_dir),
			'--statistics',
			'--use-fuzzy'
		]
		self.run_command(cmd)

	def show_menu(self):
		"""Show interactive menu and get user choice"""
		print('=' * 48)
		print('        DV-Helper Translation Management')
		print('=' * 48)
		print()
		print('1. Update All Translations')
		print('2. Initialize a New Translation')
		print('3. Compile Translation Files')
		print()
		print('=' * 48)

		# Get user choice with default
		choice = input('Please enter your choice [1-3] (default: 1): ').strip()
		if not choice:
			choice = '1'

		return choice

	def process_args(self):
		"""Process command line arguments"""
		if len(sys.argv) == 1:
			# No arguments, show interactive menu
			choice = self.show_menu()
			self.execute_choice(choice)
		else:
			# Process command line arguments
			command = sys.argv[1].lower()

			if command in ('1', 'update'):
				self.update_translations()
			elif command in ('2', 'create'):
				lang = sys.argv[2] if len(sys.argv) > 2 else None
				self.create_translation(lang)
			elif command in ('3', 'compile'):
				self.compile_translations()
			else:
				print('Invalid command. Use: update, create, or compile.')
				print('For interactive menu, run without arguments.')
				sys.exit(1)

	def execute_choice(self, choice: str):
		"""Execute the chosen menu option"""
		if choice == '1':
			self.update_translations()
		elif choice == '2':
			self.create_translation()
		elif choice == '3':
			self.compile_translations()
		else:
			print('Invalid choice. Please try again.')
			self.process_args()


if __name__ == '__main__':
	try:
		manager = TranslationManager()
		manager.process_args()
	except KeyboardInterrupt:
		pass
