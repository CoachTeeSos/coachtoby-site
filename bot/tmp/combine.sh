#!/bin/bash
# Combine both result files and prepare for Airtable
cat "$HOME/.hermes/coachtoby-site/bot/tmp/reddit_posts.jsonl" "$HOME/.hermes/coachtoby-site/bot/tmp/reddit_posts2.jsonl" > "$HOME/.hermes/coachtoby-site/bot/tmp/all_posts.jsonl"
echo "Combined posts:"
wc -l "$HOME/.hermes/coachtoby-site/bot/tmp/all_posts.jsonl"
