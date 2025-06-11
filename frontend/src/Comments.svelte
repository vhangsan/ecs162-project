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

    try {
      const response = await fetch(`${backendBase}/api/recipes/${recipeId}/comments`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ text: newComment })
      });

      const data = await response.json();

      if (data.success) {
        newComment = '';
        loadComments();
      } else {
        console.error('Failed to post comment');
      }
    } catch (err) {
      console.error('Error posting comment', err);
    }
  }

  async function deleteComment(commentId: number) {
    try {
      const response = await fetch(`${backendBase}/api/comments/${commentId}`, {
        method: 'DELETE',
        credentials: 'include'
      });
      const data = await response.json();

      if (data.success) {
        loadComments();
      } else {
        console.error('Failed to delete comment');
      }
    } catch (err) {
      console.error('Error deleting comment', err);
    }
  }
</script>

<h3>Comments</h3>

{#if comments.length > 0}
  {#each comments as comment (comment.id)}
    <div class="comment">
      <p><strong>{comment.user.username}:</strong> {comment.text}</p>

      {#if user && user.id === comment.user.id}
        <button on:click={() => deleteComment(comment.id)}>Delete</button>
      {/if}

    </div>
  {/each}
{:else}
  <p>No comments yet.</p>
{/if}

{#if user}
  <div>
    <textarea bind:value={newComment} placeholder="Write a comment..."></textarea>
    <button on:click={postComment}>Post Comment</button>
  </div>
{:else}
  <p>You must be logged in to comment.</p>
{/if}
