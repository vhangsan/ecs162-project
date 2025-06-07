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
  
  async function submitComment() {
    if (!newComment.trim() || !user) return;
    
    loading = true;
    error = '';
    
    try {
      const response = await fetch(`${backendBase}/api/recipes/${recipeId}/comments`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: 'include',
        body: JSON.stringify({ content: newComment.trim() })
      });
      
      const data = await response.json();
      
      if (data.success) {
        newComment = '';
        await loadComments(); 
      } else {
        error = data.error || 'Failed to post comment';
      }
    } catch (err) {
      error = 'Error posting comment';
      console.error(err);
    } finally {
      loading = false;
    }
  }
  
  function formatDate(dateString: string) {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  }
</script>

<div class="comments-section">
  <h3>Comments ({comments.length})</h3>
  
  {#if error}
    <div class="error-message">
      {error}
    </div>
  {/if}
  
  {#if user}
    <div class="add-comment-form">
      <textarea
        bind:value={newComment}
        placeholder="Share your thoughts about this recipe..."
        class="comment-textarea"
        rows="3"
        maxlength="1000"
        disabled={loading}
      ></textarea>
      <div class="comment-form-footer">
        <span class="character-count">{newComment.length}/1000</span>
        <button
          on:click={submitComment}
          disabled={!newComment.trim() || loading}
          class="submit-comment-btn"
        >
          {loading ? 'Posting...' : 'Post Comment'}
        </button>
      </div>
    </div>
  {:else}
    <div class="login-prompt">
      <p>Please log in to leave a comment</p>
    </div>
  {/if}
  
  <div class="comments-list">
    {#each comments as comment}
      <div class="comment-item">
        <div class="comment-header">
          <div class="commenter-avatar">
            {comment.user_email.charAt(0).toUpperCase()}
          </div>
          <div class="commenter-info">
            <span class="commenter-name">{comment.user_email}</span>
            <span class="comment-date">
              {formatDate(comment.created_at)}
            </span>
          </div>
        </div>
        
        <p class="comment-text">{comment.content}</p>
      </div>
    {/each}
    
    {#if comments.length === 0}
      <div class="no-comments">
        No comments yet. Be the first to share your thoughts!
      </div>
    {/if}
  </div>
</div>

<style>
  .comments-section {
    background: white;
    border-radius: 15px;
    padding: 2rem;
    margin-top: 2rem;
  }
  
  .comments-section h3 {
    color: #4a6741;
    font-size: 1.8rem;
    margin-bottom: 1.5rem;
  }
  
  .error-message {
    background: #fee2e2;
    border: 1px solid #f87171;
    color: #b91c1c;
    padding: 0.75rem 1rem;
    border-radius: 8px;
    margin-bottom: 1rem;
  }
  
  .add-comment-form {
    background: #f9f9f9;
    border-radius: 10px;
    padding: 1.5rem;
    margin-bottom: 2rem;
  }
  
  .comment-textarea {
    width: 100%;
    min-height: 100px;
    border: 1px solid #ddd;
    border-radius: 8px;
    padding: 1rem;
    resize: vertical;
    font-family: inherit;
    margin-bottom: 1rem;
    font-size: 1rem;
  }
  
  .comment-textarea:focus {
    outline: none;
    border-color: #4a6741;
  }
  
  .comment-form-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .character-count {
    font-size: 0.9rem;
    color: #666;
  }
  
  .submit-comment-btn {
    background: #4a6741;
    color: white;
    border: none;
    padding: 0.8rem 2rem;
    border-radius: 8px;
    font-weight: bold;
    cursor: pointer;
    font-size: 1rem;
  }
  
  .submit-comment-btn:hover:not(:disabled) {
    background: #3d5537;
  }
  
  .submit-comment-btn:disabled {
    background: #ccc;
    cursor: not-allowed;
  }
  
  .login-prompt {
    background: #f3f4f6;
    padding: 1.5rem;
    border-radius: 10px;
    text-align: center;
    margin-bottom: 2rem;
  }
  
  .login-prompt p {
    color: #666;
    margin: 0;
  }
  
  .comments-list {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }
  
  .comment-item {
    border-bottom: 1px solid #eee;
    padding-bottom: 1.5rem;
  }
  
  .comment-item:last-child {
    border-bottom: none;
    padding-bottom: 0;
  }
  
  .comment-header {
    display: flex;
    gap: 1rem;
    margin-bottom: 1rem;
    align-items: center;
  }
  
  .commenter-avatar {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    background: #4a6741;
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
    font-size: 1.1rem;
  }
  
  .commenter-info {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }
  
  .commenter-name {
    font-weight: bold;
    color: #333;
  }
  
  .comment-date {
    font-size: 0.9rem;
    color: #666;
  }
  
  .comment-text {
    color: #333;
    line-height: 1.6;
    margin: 0;
    white-space: pre-wrap;
  }
  
  .no-comments {
    text-align: center;
    color: #666;
    padding: 3rem 0;
    font-style: italic;
  }
  
  /* Mobile responsiveness */
  @media (max-width: 768px) {
    .comments-section {
      padding: 1rem;
      margin-top: 1rem;
    }
    
    .add-comment-form {
      padding: 1rem;
    }
    
    .comment-form-footer {
      flex-direction: column;
      gap: 1rem;
      align-items: stretch;
    }
    
    .submit-comment-btn {
      width: 100%;
    }
  }
</style>