"use client";

import type { KOLPost } from "@/lib/types/kol";
import { MessageSquare, Repeat2, Heart } from "lucide-react";

function formatCount(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return String(n);
}

function timeAgo(date: string): string {
  const diff = Date.now() - new Date(date).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "刚刚";
  if (mins < 60) return `${mins}分钟前`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}小时前`;
  return `${Math.floor(hours / 24)}天前`;
}

interface KOLPostsProps {
  posts: KOLPost[];
}

export function KOLPosts({ posts }: KOLPostsProps) {
  if (posts.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground text-sm">
        暂无采集数据
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {posts.map((post) => (
        <div
          key={post.id}
          className="rounded-lg border border-outline-variant/30 p-4 space-y-2"
        >
          {/* Author & time */}
          <div className="flex items-center justify-between">
            {post.author && (
              <span className="text-sm font-medium">{post.author}</span>
            )}
            <span className="text-xs text-muted-foreground">
              {timeAgo(post.collectedAt)}
            </span>
          </div>

          {/* Content */}
          <p className="text-sm leading-relaxed">{post.content}</p>

          {/* Cover image */}
          {post.coverImage && (
            <img
              src={post.coverImage}
              alt=""
              className="rounded-lg max-h-48 w-auto"
            />
          )}

          {/* Engagement */}
          <div className="flex items-center gap-4 text-xs text-muted-foreground">
            <span className="flex items-center gap-1">
              <MessageSquare className="h-3 w-3" />
              {formatCount(post.comments)}
            </span>
            <span className="flex items-center gap-1">
              <Repeat2 className="h-3 w-3" />
              {formatCount(post.shares)}
            </span>
            <span className="flex items-center gap-1">
              <Heart className="h-3 w-3" />
              {formatCount(post.likes)}
            </span>
            {post.url && (
              <a
                href={post.url}
                target="_blank"
                rel="noopener noreferrer"
                className="ml-auto text-brand hover:underline"
              >
                查看原文
              </a>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
