<script lang="ts">
  import { onMount } from 'svelte';

  export let recipeId: number;
  export let user: any = null;
  export let backendBase: string = "http://localhost:8000";

  let comments: any[] = [];
  let newComment = '';
  let loading = false;
  let error = '';

  onMount(() => {
    loadComments();
  });

  async function loadComments() {
    try {
      const response = await fetch(`${backendBase}/api/recipes/${recipeId}/comments`, {
        credentials: 'include'
      });
      const data = await response.json();

      if (data.success) {
        comments = data.comments;
      } else {
        error = 'Failed to load comments';
      }
    } catch (err) {
      error = 'Error loading comments';
      console.error(err);
    }
  }

  async function postComment() {
    if (!newComment.trim()) return;

    loading = true;
    try {
      const response = await fetch(`${backendBase}/api/recipes/${recipeId}/comments`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ content: newComment.trim() })
      });

      const data = await response.json();

      if (data.success) {
        newComment = '';
        await loadComments(); // Reload comments to get the new one
      } else {
        error = data.error || 'Failed to post comment';
      }
    } catch (err) {
      error = 'Error posting comment';
      console.error('Error posting comment', err);
    } finally {
      loading = false;
    }
  }

  async function deleteComment(commentId: string) {
    try {
      const response = await fetch(`${backendBase}/api/comments/${commentId}`, {
        method: 'DELETE',
        credentials: 'include'
      });
      
      if (response.ok) {
        await loadComments(); // Reload comments after deletion
      } else {
        error = 'Failed to delete comment';
      }
    } catch (err) {
      error = 'Error deleting comment';
      console.error('Error deleting comment', err);
    }
  }
</script>

<div class="comments-section">
  {#if user}
  {:else}
    <p class="login-prompt">You must be logged in to comment.</p>
  {/if}
</div>

<style>
  .comments-section {
    margin-top: 2rem;
  }

  .comments-section h3 {
    color: #2d5a27;
    margin-bottom: 1.5rem;
    font-size: 1.3rem;
    font-weight: 600;
  }

  .error-message {
    background: #fee;
    color: #c53030;
    padding: 1rem;
    border-radius: 8px;
    margin-bottom: 1rem;
    border: 1px solid #feb2b2;
  }

  .comments-list {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
    margin-bottom: 2rem;
  }

  .comment {
    background: rgba(245, 241, 232, 0.3);
    border-radius: 12px;
    padding: 1.5rem;
    border-left: 4px solid #7fb069;
  }

  .comment-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.8rem;
  }

  .comment-author {
    color: #2d5a27;
    font-weight: 600;
  }

  .comment-date {
    color: #5d6d7e;
    font-size: 0.9rem;
  }

  .comment-content {
    color: #2c3e50;
    line-height: 1.6;
    margin: 0;
  }

  .delete-comment-btn {
    background: #dc2626;
    color: white;
    border: none;
    padding: 0.5rem 1rem;
    border-radius: 6px;
    cursor: pointer;
    font-size: 0.9rem;
    margin-top: 1rem;
    transition: background-color 0.2s;
  }

  .delete-comment-btn:hover {
    background: #b91c1c;
  }

  .no-comments {
    color: #5d6d7e;
    font-style: italic;
    text-align: center;
    padding: 2rem;
    background: rgba(245, 241, 232, 0.2);
    border-radius: 12px;
    margin-bottom: 2rem;
  }

  .comment-form {
    background: rgba(255, 255, 255, 0.8);
    border: 2px solid rgba(45, 90, 39, 0.2);
    border-radius: 15px;
    padding: 1.5rem;
  }

  .comment-form textarea {
    width: 100%;
    border: 2px solid rgba(45, 90, 39, 0.2);
    border-radius: 8px;
    padding: 1rem;
    resize: vertical;
    font-family: inherit;
    margin-bottom: 1rem;
    font-size: 1rem;
  }

  .comment-form textarea:focus {
    outline: none;
    border-color: #2d5a27;
    box-shadow: 0 0 0 3px rgba(45, 90, 39, 0.1);
  }

  .comment-form textarea:disabled {
    background-color: #f7fafc;
    cursor: not-allowed;
  }

  .comment-form button {
    background: linear-gradient(135deg, #2d5a27, #4a7c59);
    color: white;
    border: none;
    padding: 0.8rem 1.5rem;
    border-radius: 8px;
    cursor: pointer;
    font-weight: 500;
    transition: all 0.3s ease;
    font-size: 1rem;
  }

  .comment-form button:hover:not(:disabled) {
    background: linear-gradient(135deg, #4a7c59, #7fb069);
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(45, 90, 39, 0.3);
  }

  .comment-form button:disabled {
    background: #9ca3af;
    cursor: not-allowed;
    transform: none;
    box-shadow: none;
  }

  .login-prompt {
    color: #5d6d7e;
    text-align: center;
    padding: 1.5rem;
    background: rgba(245, 241, 232, 0.2);
    border-radius: 12px;
    font-style: italic;
  }
</style>