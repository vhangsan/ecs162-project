<script lang="ts">
  import './app.css';
  import { onMount } from "svelte";
  import Comments from './Comments.svelte';

  let ingredients: string = "";
  let ingredientList: string[] = [];
  let recipes: any[] = [];
  let user: any = null;
  let selectedRecipe: any = null;
  let showRecipeModal = false;

  let loading = false;
  let searchError = "";

  let showAccountSidebar = false;

  let userRating = 0;
  let userReview = "";
  let showReviewForm = false;

  let selectedMealType = "";
  let selectedTime = "";
  let selectedDiet = "";
  let selectedIntolerances: string[] = [];
  let selectedCuisine = "";
  let activeDropdown = "";

  let availableCuisines: string[] = [];
  let availableDiets: string[] = [];
  let availableIntolerances: string[] = [];
  let availableMealTypes: string[] = [];

  let activeTab = "ingredients";
  let specificRecipeQuery = "";
  let specificRecipeResults: any[] = [];
  let specificRecipeLoading = false;

  let userFavorites: any[] = [];
  let userReviews: any[] = [];
  
  const timeOptions = [
    { value: "15", label: "<15 mins" },
    { value: "30", label: "<30 mins" },
    { value: "45", label: "<45 mins" },
    { value: "60", label: "<1 hour" },
    { value: "120", label: "<2 hours" }
  ];

  const mealTypeMapping = [
    { id: "main course", label: "MAIN COURSE", icon: "🍖" },
    { id: "breakfast", label: "BREAKFAST", icon: "☕" },
    { id: "dessert", label: "DESSERT", icon: "🍰" },
    { id: "appetizer", label: "APPETIZER", icon: "🥗" },
    { id: "snack", label: "SNACK", icon: "🥨" }
  ];

  let currentView = localStorage.getItem("currentView") || "home";

  const BACKEND_BASE = import.meta.env.VITE_BACKEND_BASE || "http://localhost:8000";

  onMount(() => {
    checkAuthStatus();
    loadFilterOptions();
  });

  let myReviews: any[] = [];
  async function loadMyReviews() {
    try {
      const response = await fetch(`${BACKEND_BASE}/api/users/me/reviews`, {
        credentials: 'include'
      });
      const data = await response.json();

      if (data.success) {
        myReviews = data.reviews;
      } else {
        console.error('Failed to load your reviews');
      }
    } catch (err) {
      console.error('Error loading your reviews', err);
    }
  }

  async function loadFilterOptions() {
    try {
      const [cuisinesRes, dietsRes, intolerancesRes, mealTypesRes] = await Promise.all([
        fetch(`${BACKEND_BASE}/api/cuisines`),
        fetch(`${BACKEND_BASE}/api/diets`),
        fetch(`${BACKEND_BASE}/api/intolerances`),
        fetch(`${BACKEND_BASE}/api/meal-types`)
      ]);

      availableCuisines = await cuisinesRes.json();
      availableDiets = await dietsRes.json();
      availableIntolerances = await intolerancesRes.json();
      availableMealTypes = await mealTypesRes.json();
    } catch (error) {
      console.error('Error loading filter options:', error);

      availableCuisines = ["Italian", "Thai", "Mexican", "Chinese", "American", "Indian"];
      availableDiets = ["vegetarian", "vegan", "gluten free"];
      availableIntolerances = ["dairy", "gluten", "peanut"];
      availableMealTypes = ["main course", "breakfast", "dessert"];
    }
  }

  async function checkAuthStatus() {
    try {
      const response = await fetch(`${BACKEND_BASE}/api/user/profile`, {
        method: 'GET',
        credentials: 'include'
      });
      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          user = data.user;
          await loadUserData();
        }
      }
    } catch (error) {
      console.log('User not logged in');
    }
  }

  async function loadUserData() {
    if (!user) return;
    
    try {
      // Try different possible endpoints for loading user data
      const endpoints = {
        favorites: [
          `${BACKEND_BASE}/api/user/favorites`,
          `${BACKEND_BASE}/api/favorites`,
          `${BACKEND_BASE}/api/user/profile/favorites`
        ],
        reviews: [
          `${BACKEND_BASE}/api/user/reviews`,
          `${BACKEND_BASE}/api/reviews`,
          `${BACKEND_BASE}/api/user/profile/reviews`
        ]
      };

      // Try to load favorites
      for (const endpoint of endpoints.favorites) {
        try {
          const favoritesRes = await fetch(endpoint, { 
            credentials: 'include',
            headers: { 'Accept': 'application/json' }
          });
          
          if (favoritesRes.ok) {
            const favData = await favoritesRes.json();
            userFavorites = favData.favorites || favData || [];
            console.log(`Loaded favorites from: ${endpoint}`);
            break;
          }
        } catch (error) {
          console.log(`Failed to load favorites from ${endpoint}:`, error);
        }
      }

      // Try to load reviews
      for (const endpoint of endpoints.reviews) {
        try {
          const reviewsRes = await fetch(endpoint, { 
            credentials: 'include',
            headers: { 'Accept': 'application/json' }
          });
          
          if (reviewsRes.ok) {
            const reviewData = await reviewsRes.json();
            userReviews = reviewData.reviews || reviewData || [];
            console.log(`Loaded reviews from: ${endpoint}`);
            break;
          }
        } catch (error) {
          console.log(`Failed to load reviews from ${endpoint}:`, error);
        }
      }
    } catch (error) {
      console.error('Error loading user data:', error);
    }
  }

  function login() {
    window.location.href = `${BACKEND_BASE}/login`;
  }

  function logout() {
    window.location.href = `${BACKEND_BASE}/logout`;
  }

  function addIngredient() {
    const trimmed = ingredients.trim().toLowerCase();
    if (trimmed && !ingredientList.includes(trimmed)) {
      ingredientList = [...ingredientList, trimmed];
      ingredients = "";
    }
  }

  function removeIngredient(ing: string) {
    ingredientList = ingredientList.filter(i => i !== ing);
    if (ingredientList.length > 0) {
      searchRecipes();
    } else {
      recipes = [];
    }
  }

  async function searchRecipes() {
    loading = true;
    searchError = "";
    
    try {
      let searchTerm = "";
      if (ingredientList.length > 0) {
        searchTerm = ingredientList.join(',');
      } else if (ingredients.trim()) {
        searchTerm = ingredients.trim().toLowerCase();
      } else {
        recipes = [];
        loading = false;
        return;
      }

      const params = new URLSearchParams({
        ingredients: searchTerm
      });

      if (selectedCuisine) params.append('cuisine', selectedCuisine);
      if (selectedDiet) params.append('diet', selectedDiet);
      if (selectedIntolerances.length > 0) params.append('intolerances', selectedIntolerances.join(','));
      if (selectedTime) params.append('maxReadyTime', selectedTime);
      if (selectedMealType) params.append('type', selectedMealType);

      params.append('number', '6');

      const url = `${BACKEND_BASE}/recipes?${params.toString()}`;
      const res = await fetch(url);
      
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}: ${res.statusText}`);
      }

      const recipeResults = await res.json();

      if (!Array.isArray(recipeResults)) {
        searchError = recipeResults.error || "Invalid response format";
        recipes = [];
        loading = false;
        return;
      }

      if (recipeResults.length === 0) {
        searchError = "No recipes found for these ingredients. Try different ingredients or remove some filters.";
        recipes = [];
        loading = false;
        return;
      }

      recipes = recipeResults.map((r: any) => ({
        id: r.id,
        title: r.title || `Recipe ${r.id}`,
        image: r.image || '/Temp_Image.jpg', 
        calories: r.calories || r.nutrition?.nutrients?.find((n: any) => n.name === 'Calories')?.amount || 0,
        rating: r.spoonacularScore !== undefined ? Math.round(r.spoonacularScore / 20 * 10) / 10 : 3.0,
        cuisines: r.cuisines && r.cuisines.length > 0 ? r.cuisines : ["International"],
        readyInMinutes: r.readyInMinutes || 30,
        servings: r.servings || 1,
        vegetarian: r.vegetarian || false,
        vegan: r.vegan || false,
        glutenFree: r.glutenFree || false,
        dairyFree: r.dairyFree || false,
        dishTypes: r.dishTypes || ["main course"],
        extendedIngredients: r.extendedIngredients || [],
        analyzedInstructions: r.analyzedInstructions || [],
        nutrition: r.nutrition || {
          nutrients: [
            { name: "Calories", amount: r.calories || 0, unit: "kcal" },
            { name: "Fat", amount: 0, unit: "g" },
            { name: "Carbohydrates", amount: 0, unit: "g" },
            { name: "Protein", amount: 0, unit: "g" }
          ]
        }
      }));
      
    } catch (error) {
      console.error("Error fetching recipes:", error);
      searchError = `Failed to fetch recipes: ${(error as Error).message}`;
      recipes = [];
    } finally {
      loading = false;
    }
  }

  async function searchSpecificRecipe() {
    if (!specificRecipeQuery.trim()) return;
    
    specificRecipeLoading = true;
    searchError = "";
    
    try {
      const params = new URLSearchParams({
        query: specificRecipeQuery.trim(),
        number: '6'
      });

      const url = `${BACKEND_BASE}/recipes?${params.toString()}`;
      const res = await fetch(url);
      
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}: ${res.statusText}`);
      }

      const results = await res.json();
      
      if (!Array.isArray(results)) {
        searchError = results.error || "Invalid response format";
        specificRecipeResults = [];
        return;
      }

      if (results.length === 0) {
        searchError = "No recipes found for this search. Try different keywords.";
        specificRecipeResults = [];
        return;
      }

      specificRecipeResults = results.map((r: any) => ({
        id: r.id,
        title: r.title || `Recipe ${r.id}`,
        image: r.image || '/Temp_Image.jpg',
        calories: r.calories || r.nutrition?.nutrients?.find((n: any) => n.name === 'Calories')?.amount || 0,
        rating: r.spoonacularScore !== undefined ? Math.round(r.spoonacularScore / 20 * 10) / 10 : 3.0,
        cuisines: r.cuisines && r.cuisines.length > 0 ? r.cuisines : ["International"],
        readyInMinutes: r.readyInMinutes || 30,
        servings: r.servings || 1,
        vegetarian: r.vegetarian || false,
        vegan: r.vegan || false,
        glutenFree: r.glutenFree || false,
        dairyFree: r.dairyFree || false,
        dishTypes: r.dishTypes || ["main course"],
        extendedIngredients: r.extendedIngredients || [],
        analyzedInstructions: r.analyzedInstructions || [],
        nutrition: r.nutrition || {
          nutrients: [
            { name: "Calories", amount: r.calories || 0, unit: "kcal" },
            { name: "Fat", amount: 0, unit: "g" },
            { name: "Carbohydrates", amount: 0, unit: "g" },
            { name: "Protein", amount: 0, unit: "g" }
          ]
        }
      }));
      
    } catch (error) {
      console.error("Error searching specific recipes:", error);
      searchError = `Failed to search recipes: ${(error as Error).message}`;
      specificRecipeResults = [];
    } finally {
      specificRecipeLoading = false;
    }
  }

  function switchTab(tab: string) {
    activeTab = tab;
    if (tab === "ingredients") {
      specificRecipeResults = [];
      specificRecipeQuery = "";
    } else {
      recipes = [];
      ingredientList = [];
      ingredients = "";
    }
    searchError = "";
  }

  async function toggleFavorite(recipe: any) {
    if (!user) {
      alert('Please log in to favorite recipes');
      return;
    }

    try {
      const isFavorited = userFavorites.some(fav => fav.id === recipe.id);
      
      // For now, just update local state until backend endpoints are ready
      if (isFavorited) {
        userFavorites = userFavorites.filter(fav => fav.id !== recipe.id);
        console.log('Removed from favorites (local only)');
      } else {
        userFavorites = [...userFavorites, recipe];
        console.log('Added to favorites (local only)');
      }

      // TODO: Remove this block once backend endpoints are implemented
      alert(`Recipe ${isFavorited ? 'removed from' : 'added to'} favorites! (This is currently stored locally only)`);
      
      // Uncomment this section once your backend has the correct endpoints:
      /*
      const response = await fetch(`${BACKEND_BASE}/api/favorites${isFavorited ? `/${recipe.id}` : ''}`, {
        method: isFavorited ? 'DELETE' : 'POST',
        credentials: 'include',
        headers: { 
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        ...(isFavorited ? {} : { body: JSON.stringify({ recipeId: recipe.id, recipe: recipe }) })
      });

      if (!response.ok) {
        // Revert the local change if backend fails
        if (isFavorited) {
          userFavorites = [...userFavorites, recipe];
        } else {
          userFavorites = userFavorites.filter(fav => fav.id !== recipe.id);
        }
        throw new Error(`HTTP ${response.status}`);
      }
      */
      
    } catch (error) {
      console.error('Error toggling favorite:', error);
      alert('Favorites feature is not yet implemented on the backend.');
    }
  }

  function isRecipeFavorited(recipeId: number): boolean {
    return userFavorites.some(fav => fav.id === recipeId);
  }

  async function submitReviewWithRating() {
    if (!user) {
      alert('Please log in to submit reviews');
      return;
    }
    
    if (userRating === 0) {
      alert('Please select a rating');
      return;
    }
    
    if (!userReview.trim()) {
      alert('Please write a review');
      return;
    }

    try {
      // For now, just update local state until backend endpoints are ready
      const newReview = {
        id: Date.now(),
        recipeId: selectedRecipe.id,
        rating: userRating,
        review: userReview.trim(),
        createdAt: new Date().toISOString(),
        userEmail: user.email
      };
      
      userReviews = [...userReviews, newReview];
      showReviewForm = false;
      userRating = 0;
      userReview = "";
      
      alert('Review submitted! (This is currently stored locally only)');
      console.log('Review submitted (local only):', newReview);
      
      // TODO: Remove this block once backend endpoints are implemented
      // Uncomment this section once your backend has the correct endpoints:
      /*
      const response = await fetch(`${BACKEND_BASE}/api/reviews`, {
        method: 'POST',
        credentials: 'include',
        headers: { 
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({
          recipeId: selectedRecipe.id,
          rating: userRating,
          review: userReview.trim(),
          recipeTitle: selectedRecipe.title
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      
      const result = await response.json();
      // Update with backend response
      */
      
    } catch (error) {
      console.error('Error submitting review:', error);
      alert('Reviews feature is not yet implemented on the backend.');
    }
  }

  function toggleDropdown(dropdown: string) {
    activeDropdown = activeDropdown === dropdown ? "" : dropdown;
  }

  function reapplyFilters() {
    if (ingredientList.length > 0 || ingredients.trim()) {
      searchRecipes();
    }
  }

  function toggleMealType(mealType: string) {
    selectedMealType = selectedMealType === mealType ? "" : mealType;
    reapplyFilters();
  }

  function selectFilter(filterType: string, value: string) {
    switch(filterType) {
      case 'time':
        selectedTime = selectedTime === value ? "" : value;
        break;
      case 'diet':
        selectedDiet = selectedDiet === value ? "" : value;
        break;
      case 'cuisine':
        selectedCuisine = selectedCuisine === value ? "" : value;
        break;
    }
    activeDropdown = "";
    reapplyFilters();
  }

  function toggleIntolerance(intolerance: string) {
    if (selectedIntolerances.includes(intolerance)) {
      selectedIntolerances = selectedIntolerances.filter(i => i !== intolerance);
    } else {
      selectedIntolerances = [...selectedIntolerances, intolerance];
    }
    reapplyFilters();
  }

  function clearAllFilters() {
    selectedMealType = "";
    selectedTime = "";
    selectedDiet = "";
    selectedIntolerances = [];
    selectedCuisine = "";
    activeDropdown = "";
    reapplyFilters();
  }

  function openRecipeModal(recipe: any) {
    selectedRecipe = recipe;
    showRecipeModal = true;
    userRating = 0;
    userReview = "";
    showReviewForm = false;
  }

  function closeRecipeModal() {
    showRecipeModal = false;
    selectedRecipe = null;
  }

  function renderStars(rating: number) {
    const fullStars = Math.floor(rating);
    const hasHalfStar = rating - fullStars >= 0.5;
    let stars = '';
    for (let i = 0; i < 5; i++) {
      if (i < fullStars) {
        stars += '★';
      } else if (i === fullStars && hasHalfStar) {
        stars += '☆';
      } else {
        stars += '☆';
      }
    }
    return stars;
  }

  function setRating(rating: number) {
    userRating = rating;
  }

  function getNutrientValue(nutrients: any[], name: string): number {
    const nutrient = nutrients.find(n => n.name === name);
    return nutrient ? Math.round(nutrient.amount) : 0;
  }

  function handleImageError(event: Event) {
    const target = event.target as HTMLImageElement;
    if (target && target.src !== '/Temp_Image.jpg') {
      console.log(`Image failed to load:`, target.src);
      target.src = '/Temp_Image.jpg';
    }
  }

  function showHome() {
    currentView = "home";
    localStorage.setItem("currentView", currentView);
    showAccountSidebar = false;
  }

  function showFavorites() {
    currentView = "favorites";
    localStorage.setItem("currentView", currentView);
    showAccountSidebar = false;
  }

  function showReviews() {
    currentView = "reviews";
    localStorage.setItem("currentView", currentView);
    showAccountSidebar = false;
  }
</script>

<main class="figma-main">
  <!-- HEADER -->
  <header class="figma-header">
    <div class="header-content">
      <button class="website-title" on:click={showHome}>
        🍽️ whisk
      </button>
      <div class="header-nav">
        <button class="nav-button" on:click={showHome}>
          Home
        </button>
        {#if user}
          <div class="user-menu">
            <button class="nav-button" on:click={() => (showAccountSidebar = !showAccountSidebar)}>
              👤 Account ▾
            </button>
            {#if showAccountSidebar}
              <div class="dropdown-menu">
                <div class="user-email">{user.email}</div>
                <button class="favorites-btn link-button" on:click={showFavorites}>⭐ My Favorites</button>
                <button class="reviews-btn link-button" on:click={showReviews}>📝 My Reviews</button>
                <button class="logout-btn link-button" on:click={logout}>
                  🚪 Logout
                </button>
              </div>
            {/if}
          </div>
        {:else}
          <button class="nav-button" on:click={login}>
            Login
          </button>
        {/if}
      </div>
    </div>
  </header>

  {#if currentView === "home"}
    <slot></slot>
  {/if}

  {#if currentView === "favorites"}
    <section class="favorites-section">
      <h2 class="section-title">
        <span class="title-icon">⭐</span>
        MY FAVORITES ({userFavorites.length})
      </h2>
      {#if userFavorites.length === 0}
        <p class="empty-message">You have no favorited recipes yet.</p>
      {:else}
        <div class="recipes-grid">
          {#each userFavorites as recipe, index}
            <div 
              class="recipe-card clickable"
              style="animation-delay: {index * 0.1}s"
              on:click={() => openRecipeModal(recipe)}
              tabindex="0"
            >
              <div class="recipe-image-container">
                <img 
                  src={recipe.image} 
                  alt={recipe.title} 
                  class="recipe-image"
                  on:error={handleImageError}
                />
                <div class="recipe-overlay">
                  <button class="quick-view-btn">
                    <span class="btn-icon">👁️</span>
                    View Recipe
                  </button>
                </div>
                <button
                  class="favorite-heart favorited"
                  on:click|stopPropagation={() => toggleFavorite(recipe)}
                >
                  ❤️
                </button>
              </div>
              <div class="recipe-info">
                <h3 class="recipe-title">{recipe.title.toUpperCase()}</h3>
                <div class="rating-stars">{renderStars(recipe.rating)}</div>
                <div class="recipe-meta">
                  <span class="cuisine">
                    <span class="meta-icon">🌍</span>
                    {recipe.cuisines[0]}
                  </span>
                  <span class="calories">
                    <span class="meta-icon">🔥</span>
                    {recipe.calories} cal
                  </span>
                </div>
              </div>
            </div>
          {/each}
        </div>
      {/if}
    </section>
  {/if}

  {#if currentView === "reviews"}
    <section class="favorites-section">
      <h2 class="section-title">
        <span class="title-icon">📝</span>
        MY REVIEWS ({userReviews.length})
      </h2>
      {#if userReviews.length === 0}
        <p class="empty-message">You have not written any reviews yet.</p>
      {:else}
        <div class="reviews-list">
          {#each userReviews as review}
            <div class="review-item">
              <div class="review-header">
                <div class="review-rating">{renderStars(review.rating)}</div>
                <span class="review-date">{new Date(review.createdAt).toLocaleDateString()}</span>
              </div>
              <p class="review-text">{review.review}</p>
            </div>
          {/each}
        </div>
      {/if}
    </section>
  {/if}

  <!-- HERO SECTION -->
  <section class="hero-section">
    <div class="hero-content">
      <h2 class="hero-title">You bring the ingredients, we bring the recipes</h2>
      <p class="hero-subtitle">Recipes built around what's left in your fridge — don't waste it, taste it.</p>
    </div>
  </section>

  <!-- SEARCH SECTION -->
  <section class="search-section">
    <div class="search-tabs">
      <button class="tab-button {activeTab === 'ingredients' ? 'active' : ''}" on:click={() => switchTab('ingredients')}>
        Use My Ingredients
      </button>
      <button class="tab-button {activeTab === 'specific' ? 'active' : ''}" on:click={() => switchTab('specific')}>
        Find Specific Recipe
      </button>
    </div>

    {#if activeTab === 'ingredients'}
      <div class="search-container">
        <input
          type="text"
          bind:value={ingredients}
          placeholder="Enter ingredients (e.g., chicken, rice, vegetables)..."
          class="search-input"
          on:keydown={e => {
            if (e.key === 'Enter') {
              e.preventDefault();
              if (ingredients.trim()) {
                addIngredient();
                if (ingredientList.length > 0) searchRecipes();
              }
            }
          }}
        />
        <button class="search-btn" on:click={() => {
          if (ingredients.trim()) {
            addIngredient();
            if (ingredientList.length > 0) searchRecipes();
          } else if (ingredientList.length > 0) {
            searchRecipes();
          }
        }} disabled={loading}>
          {#if loading}
            <span class="spinner">⏳</span>
          {:else}
            <span class="search-icon">🔍</span>
          {/if}
        </button>
      </div>
      {#if ingredientList.length > 0 || ingredients.trim()}
        <div class="ingredient-tags">
          {#each ingredientList as ing}
            <span class="ingredient-tag">
              {ing.toUpperCase()}
              <button class="remove-tag" on:click={() => removeIngredient(ing)}>×</button>
            </span>
          {/each}
          {#if ingredients.trim() && !ingredientList.includes(ingredients.trim().toLowerCase())}
            <span class="ingredient-tag pending">
              {ingredients.toUpperCase()} (press enter to add)
            </span>
          {/if}
        </div>
      {/if}
    {:else}
      <div class="search-container">
        <input
          type="text"
          bind:value={specificRecipeQuery}
          placeholder="Search for specific recipes (e.g., 'chocolate cake', 'chicken curry')..."
          class="search-input"
          on:keydown={e => {
            if (e.key === 'Enter') {
              e.preventDefault();
              searchSpecificRecipe();
            }
          }}
        />
        <button class="search-btn" on:click={searchSpecificRecipe} disabled={specificRecipeLoading}>
          {#if specificRecipeLoading}
            <span class="spinner">⏳</span>
          {:else}
            <span class="search-icon">🔍</span>
          {/if}
        </button>
      </div>
    {/if}
    
    {#if loading || specificRecipeLoading}
      <div class="debug-info loading">
        <span class="spinner">⏳</span>
        Searching for delicious recipes...
      </div>
    {/if}
    
    {#if searchError}
      <div class="debug-info error">
        ⚠️ {searchError}
      </div>
    {/if}
    
    {#if (activeTab === 'ingredients' && recipes.length === 0 && !loading && !searchError && ingredientList.length > 0) || 
         (activeTab === 'specific' && specificRecipeResults.length === 0 && !specificRecipeLoading && !searchError && specificRecipeQuery.trim())}
      <div class="debug-info warning">
        ℹ️ No recipes found. Try different {activeTab === 'ingredients' ? 'ingredients' : 'search terms'}.
      </div>
    {/if}
  </section>

  {#if ingredientList.length > 0 && activeTab === 'ingredients'}
    <section class="filters-section">
      <div class="filters-container">
        <div class="ingredient-display">
          <h3>
            <span class="section-icon">🌱</span>
            MY INGREDIENTS:
          </h3>
          <div class="current-ingredients">
            {#each ingredientList as ing}
              <span class="ingredient-tag">
                <span class="tag-icon">🥬</span>
                {ing.toUpperCase()}
                <button class="remove-tag" on:click={() => removeIngredient(ing)}>
                  <span class="close-icon">×</span>
                </button>
              </span>
            {/each}
          </div>
        </div>
        <div class="meal-type-section">
          <div class="meal-type-grid">
            {#each mealTypeMapping as mealType}
              <button 
                class="meal-type-card {selectedMealType === mealType.id ? 'selected' : ''}"
                on:click={() => toggleMealType(mealType.id)}
              >
                <div class="meal-icon">{mealType.icon}</div>
                <div class="meal-label">{mealType.label}</div>
              </button>
            {/each}
          </div>
        </div>
        <div class="filter-dropdowns">
          <div class="filter-dropdown">
            <button class="filter-btn {selectedTime ? 'active' : ''}" on:click={() => toggleDropdown('time')}>
              <span class="filter-icon">⏰</span>
              <span class="filter-text">TIME</span>
              <span class="dropdown-arrow">▼</span>
            </button>
            {#if activeDropdown === 'time'}
              <div class="dropdown-content">
                {#each timeOptions as option}
                  <button 
                    class="dropdown-option {selectedTime === option.value ? 'selected' : ''}"
                    on:click={() => selectFilter('time', option.value)}
                  >
                    <span class="option-icon">⏰</span>
                    <span class="option-text">{option.label}</span>
                  </button>
                {/each}
              </div>
            {/if}
          </div>
          <div class="filter-dropdown">
            <button class="filter-btn {selectedDiet ? 'active' : ''}" on:click={() => toggleDropdown('diet')}>
              <span class="filter-icon">🌱</span>
              <span class="filter-text">DIET</span>
              <span class="dropdown-arrow">▼</span>
            </button>
            {#if activeDropdown === 'diet'}
              <div class="dropdown-content">
                {#each availableDiets as option}
                  <button 
                    class="dropdown-option {selectedDiet === option ? 'selected' : ''}"
                    on:click={() => selectFilter('diet', option)}
                  >
                    <span class="option-icon">🌱</span>
                    <span class="option-text">{option}</span>
                  </button>
                {/each}
              </div>
            {/if}
          </div>
          <div class="filter-dropdown">
            <button class="filter-btn {selectedIntolerances.length > 0 ? 'active' : ''}" on:click={() => toggleDropdown('intolerance')}>
              <span class="filter-icon">🛡️</span>
              <span class="filter-text">INTOLERANCES</span>
              <span class="dropdown-arrow">▼</span>
            </button>
            {#if activeDropdown === 'intolerance'}
              <div class="dropdown-content">
                {#each availableIntolerances as option}
                  <button 
                    class="dropdown-option {selectedIntolerances.includes(option) ? 'selected' : ''}"
                    on:click={() => toggleIntolerance(option)}
                  >
                    <span class="option-icon">🛡️</span>
                    <span class="option-text">{option} {selectedIntolerances.includes(option) ? '✓' : ''}</span>
                  </button>
                {/each}
              </div>
            {/if}
          </div>
          <div class="filter-dropdown">
            <button class="filter-btn {selectedCuisine ? 'active' : ''}" on:click={() => toggleDropdown('cuisine')}>
              <span class="filter-icon">🌍</span>
              <span class="filter-text">CUISINE</span>
              <span class="dropdown-arrow">▼</span>
            </button>
            {#if activeDropdown === 'cuisine'}
              <div class="dropdown-content">
{#each availableCuisines as option}
                 <button 
                   class="dropdown-option {selectedCuisine === option ? 'selected' : ''}"
                   on:click={() => selectFilter('cuisine', option)}
                 >
                   <span class="option-icon">🌍</span>
                   <span class="option-text">{option}</span>
                 </button>
               {/each}
             </div>
           {/if}
         </div>
       </div>
       {#if selectedTime || selectedDiet || selectedIntolerances.length > 0 || selectedCuisine || selectedMealType}
         <div class="active-filters">
           <span class="filter-label">
             <span class="filter-label-icon">🔗</span>
             Active filters:
           </span>
           {#if selectedMealType}
             <span class="active-filter-tag">
               {mealTypeMapping.find(m => m.id === selectedMealType)?.label}
               <button on:click={() => toggleMealType(selectedMealType)}>×</button>
             </span>
           {/if}
           {#if selectedTime}
             <span class="active-filter-tag">
               {timeOptions.find(t => t.value === selectedTime)?.label}
               <button on:click={() => selectFilter('time', selectedTime)}>×</button>
             </span>
           {/if}
           {#if selectedDiet}
             <span class="active-filter-tag">
               {selectedDiet}
               <button on:click={() => selectFilter('diet', selectedDiet)}>×</button>
             </span>
           {/if}
           {#each selectedIntolerances as intolerance}
             <span class="active-filter-tag">
               {intolerance}
               <button on:click={() => toggleIntolerance(intolerance)}>×</button>
             </span>
           {/each}
           {#if selectedCuisine}
             <span class="active-filter-tag">
               {selectedCuisine}
               <button on:click={() => selectFilter('cuisine', selectedCuisine)}>×</button>
             </span>
           {/if}
           <button class="clear-filters-btn" on:click={clearAllFilters}>
             <span class="clear-icon">🧹</span>
             Clear All
           </button>
         </div>
       {/if}
     </div>
   </section>
 {/if}

 <!-- RECIPE RESULTS -->
 {#if (activeTab === 'ingredients' && recipes.length > 0) || (activeTab === 'specific' && specificRecipeResults.length > 0)}
   <section class="results-section">
     <h2 class="section-title">
       <span class="title-icon">🍽️</span>
       RECIPE RESULTS ({activeTab === 'ingredients' ? recipes.length : specificRecipeResults.length})
     </h2>
     <div class="recipes-grid">
       {#each (activeTab === 'ingredients' ? recipes : specificRecipeResults) as recipe, index}
         <div 
           class="recipe-card clickable" 
           style="animation-delay: {index * 0.1}s"
           on:click={() => openRecipeModal(recipe)} 
           on:keydown={(e) => e.key === 'Enter' && openRecipeModal(recipe)} 
           tabindex="0"
         >
           <div class="recipe-image-container">
             <img 
               src={recipe.image} 
               alt={recipe.title} 
               class="recipe-image" 
               on:error={handleImageError}
             />
             <div class="recipe-overlay">
               <button class="quick-view-btn">
                 <span class="btn-icon">👁️</span>
                 View Recipe
               </button>
             </div>
             {#if user}
               <button 
                 class="favorite-heart {isRecipeFavorited(recipe.id) ? 'favorited' : ''}"
                 on:click|stopPropagation={() => toggleFavorite(recipe)}
               >
                 {isRecipeFavorited(recipe.id) ? '❤️' : '🤍'}
               </button>
             {/if}
           </div>
           <div class="recipe-info">
             <h3 class="recipe-title">{recipe.title.toUpperCase()}</h3>
             <div class="rating-stars">{renderStars(recipe.rating)}</div>
             <div class="recipe-meta">
               <span class="cuisine">
                 <span class="meta-icon">🌍</span>
                 {recipe.cuisines[0]}
               </span>
               <span class="calories">
                 <span class="meta-icon">🔥</span>
                 {recipe.calories} cal
               </span>
             </div>
             {#if recipe.vegan}
               <div class="dietary-badge vegan">V</div>
             {/if}
             {#if recipe.glutenFree}
               <div class="dietary-badge gluten-free">GF</div>
             {/if}
           </div>
         </div>
       {/each}
     </div>
   </section>
 {/if}

 <!-- RECIPE MODAL - FULL SCREEN WITH UNIFORM FONTS -->
 {#if showRecipeModal && selectedRecipe}
   <div class="recipe-detail-modal" on:click={closeRecipeModal}>
     <div class="modal-content" on:click|stopPropagation>
       <button class="modal-close-btn" on:click={closeRecipeModal}>
         <span class="close-icon">×</span>
       </button>
       
       <div class="recipe-header-compact">
         <div class="recipe-header-content">
           <h1 class="recipe-detail-title">{selectedRecipe.title}</h1>
           
           <div class="recipe-rating-info">
             <div class="rating-display">
               <div class="rating-stars-large">{renderStars(selectedRecipe.rating)}</div>
               <span class="rating-number">{selectedRecipe.rating}</span>
               <span class="cuisine-type">| {selectedRecipe.cuisines[0]} Cuisine</span>
             </div>
           </div>
           
           <div class="recipe-stats-bar-compact">
             <div class="stat-item">
               <strong>Prep:</strong> {Math.round(selectedRecipe.readyInMinutes * 0.3)} min
             </div>
             <div class="stat-item">
               <strong>Cook:</strong> {Math.round(selectedRecipe.readyInMinutes * 0.7)} min
             </div>
             <div class="stat-item">
               <strong>Serves:</strong> {selectedRecipe.servings}
             </div>
           </div>
           
           <div class="recipe-actions">
             <button class="favorite-btn" on:click={() => toggleFavorite(selectedRecipe)}>
               <span class="heart-icon">
                 {isRecipeFavorited(selectedRecipe.id) ? '❤️' : '🤍'}
               </span>
               Favorite
             </button>
             {#if user}
               <button class="rate-btn" on:click={() => showReviewForm = !showReviewForm}>
                 <span class="star-icon">⭐</span>
                 Write Review
               </button>
             {/if}
           </div>
         </div>
       </div>
       
       <div class="recipe-scrollable-content">
         <div class="recipe-body">
           <div class="recipe-left">
             <img src={selectedRecipe.image} alt={selectedRecipe.title} class="recipe-detail-image" on:error={handleImageError} />
             
             <div class="nutrition-box">
               <h3>
                 Nutrition Info <span class="per-serving">(per serving)</span>
               </h3>
               <div class="nutrition-grid">
                 <div class="nutrition-item">
                   <span class="nutrition-value">{getNutrientValue(selectedRecipe.nutrition?.nutrients || [], 'Calories')}</span>
                   <span class="nutrition-label">Calories</span>
                 </div>
                 <div class="nutrition-item">
                   <span class="nutrition-value">{getNutrientValue(selectedRecipe.nutrition?.nutrients || [], 'Fat')}g</span>
                   <span class="nutrition-label">Fat</span>
                 </div>
                 <div class="nutrition-item">
                   <span class="nutrition-value">{getNutrientValue(selectedRecipe.nutrition?.nutrients || [], 'Carbohydrates')}g</span>
                   <span class="nutrition-label">Carbs</span>
                 </div>
                 <div class="nutrition-item">
                   <span class="nutrition-value">{getNutrientValue(selectedRecipe.nutrition?.nutrients || [], 'Protein')}g</span>
                   <span class="nutrition-label">Protein</span>
                 </div>
               </div>
             </div>
           </div>
           
           <div class="recipe-right">
             <div class="ingredients-section">
               <h2>Ingredients</h2>
               <ul class="ingredients-list">
                 {#each selectedRecipe.extendedIngredients as ing}
                   <li class="ingredient-item">
                     <span class="ingredient-measure">{ing.amount} {ing.unit}</span>
                     <span class="ingredient-name">{ing.name}</span>
                   </li>
                 {/each}
               </ul>
             </div>
             
             <div class="instructions-section">
               <h2>Instructions</h2>
               <div class="instructions-list">
                 {#if selectedRecipe.analyzedInstructions.length > 0}
                   {#each selectedRecipe.analyzedInstructions[0].steps as step}
                     <div class="instruction-step">
                       <div class="step-number">{step.number}</div>
                       <div class="step-text">{step.step}</div>
                     </div>
                   {/each}
                 {:else}
                   <p class="no-instructions">No detailed instructions available.</p>
                 {/if}
               </div>
             </div>
           </div>
         </div>
         
         <!-- Reviews Section with Rating -->
         <div class="reviews-section-detailed">
           <h2>Reviews</h2>
           
           {#if user && showReviewForm}
             <div class="add-review-form">
               <div class="rating-input">
                 <label class="rating-label">Your Rating:</label>
                 <div class="star-rating-input">
                   {#each [1, 2, 3, 4, 5] as star}
                     <button 
                       type="button"
                       class="star-btn {userRating >= star ? 'active' : ''}"
                       on:click={() => setRating(star)}
                     >
                       ★
                     </button>
                   {/each}
                 </div>
               </div>
               <textarea 
                 bind:value={userReview}
                 placeholder="Share your thoughts about this recipe..."
                 class="review-textarea"
               ></textarea>
               <div class="review-form-actions">
                 <button class="submit-review-btn" on:click={submitReviewWithRating}>
                   Submit Review
                 </button>
                 <button class="cancel-review-btn" on:click={() => showReviewForm = false}>
                   Cancel
                 </button>
               </div>
             </div>
           {/if}
           
           <!-- Display User's Reviews -->
           {#if accountView === 'reviews'}
              <h2>Your Reviews</h2>
              {#if myReviews.length > 0}
                {#each myReviews as review (review.id)}
                  <div class="review">
                    <h3>{review.recipe.title}</h3>
                    <p>{review.text}</p>
                  </div>
                {/each}
              {:else}
                <p>You have not written any reviews yet.</p>
              {/if}
            {/if}
           
           <!-- Comments Section -->
           <Comments recipeId={selectedRecipe.id} {user} backendBase={BACKEND_BASE} />
         </div>
       </div>
     </div>
   </div>
 {/if}
</main>

<style>
 /* Fix for modal blur issue */
 .recipe-detail-modal {
   position: fixed;
   top: 0;
   left: 0;
   right: 0;
   bottom: 0;
   background: rgba(0, 0, 0, 0.8);
   z-index: 9999;
   display: flex;
   align-items: center;
   justify-content: center;
   backdrop-filter: blur(5px);
 }

 .modal-content {
   background: white;
   width: 100vw;
   height: 100vh;
   border-radius: 0;
   display: flex;
   flex-direction: column;
   position: relative;
   overflow: hidden;
   box-shadow: none;
 }

 .modal-close-btn {
   position: absolute;
   top: 1rem;
   right: 1rem;
   background: rgba(0, 0, 0, 0.8);
   color: white;
   border: none;
   border-radius: 50%;
   width: 45px;
   height: 45px;
   cursor: pointer;
   z-index: 10000;
   display: flex;
   align-items: center;
   justify-content: center;
   font-size: 1.5rem;
   font-weight: bold;
   transition: all 0.3s ease;
 }

 .modal-close-btn:hover {
   background: rgba(0, 0, 0, 0.9);
   transform: scale(1.1);
 }

 .recipe-header-compact {
   background: linear-gradient(135deg, #f5f1e8, #fef7ed);
   padding: 2rem;
   border-bottom: 1px solid rgba(45, 90, 39, 0.1);
   flex-shrink: 0;
 }

 .recipe-detail-title {
   font-family: 'Playfair Display', serif;
   font-size: 1.6rem;
   font-weight: 700;
   color: #2d5a27;
   margin-bottom: 1rem;
   line-height: 1.2;
 }

 .recipe-rating-info {
   margin-bottom: 1rem;
 }

 .rating-display {
   display: flex;
   align-items: center;
   gap: 1rem;
   font-size: 1rem;
 }

 .rating-stars-large {
   font-size: 1.2rem;
   color: #f59e0b;
 }

 .rating-number {
   font-weight: bold;
   color: #2c3e50;
   font-size: 1rem;
 }

 .cuisine-type {
   color: #5d6d7e;
   font-size: 1rem;
 }

 .recipe-stats-bar-compact {
   display: flex;
   gap: 2rem;
   margin-bottom: 1rem;
   padding: 1rem;
   background: rgba(255, 255, 255, 0.8);
   border-radius: 15px;
   backdrop-filter: blur(10px);
 }

 .stat-item {
   font-size: 1rem;
   color: #2c3e50;
   display: flex;
   align-items: center;
   gap: 0.5rem;
 }

 .recipe-actions {
   display: flex;
   gap: 1rem;
 }

 .favorite-btn, .rate-btn {
   background: linear-gradient(135deg, #c8e6c9, #7fb069);
   border: none;
   padding: 0.8rem 1.5rem;
   border-radius: 20px;
   font-weight: 600;
   cursor: pointer;
   display: flex;
   align-items: center;
   gap: 0.5rem;
   transition: all 0.3s ease;
   color: #2d5a27;
   box-shadow: 0 3px 10px rgba(127, 176, 105, 0.3);
   font-size: 1rem;
 }

 .favorite-btn:hover, .rate-btn:hover {
   background: linear-gradient(135deg, #2d5a27, #4a7c59);
   color: white;
   transform: translateY(-2px);
   box-shadow: 0 6px 20px rgba(45, 90, 39, 0.4);
 }

 .favorite-btn.favorited {
   background: linear-gradient(135deg, #ff6b9d, #ff8e9b);
   color: white;
 }

 .recipe-scrollable-content {
   flex: 1;
   overflow-y: auto;
   padding: 2rem;
 }

 .recipe-body {
   display: grid;
   grid-template-columns: 1fr 1fr;
   gap: 3rem;
   margin-bottom: 3rem;
 }

 .recipe-detail-image {
   width: 100%;
   height: 400px;
   object-fit: cover;
   border-radius: 15px;
   box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
 }

 .nutrition-box {
   background: #f8f9fa;
   border: 2px solid rgba(45, 90, 39, 0.2);
   border-radius: 15px;
   padding: 2rem;
   margin-top: 2rem;
 }

 .nutrition-box h3 {
   color: #2d5a27;
   font-size: 1.2rem;
   margin-bottom: 1.5rem;
   font-weight: 600;
 }

 .per-serving {
   font-weight: normal;
   font-size: 1rem;
   color: #5d6d7e;
 }

 .nutrition-grid {
   display: grid;
   grid-template-columns: repeat(2, 1fr);
   gap: 1.5rem;
 }

 .nutrition-item {
   text-align: center;
   padding: 1rem;
   background: rgba(245, 158, 11, 0.1);
   border-radius: 10px;
 }

 .nutrition-value {
   display: block;
   font-size: 1.4rem;
   font-weight: bold;
   color: #d2691e;
 }

 .nutrition-label {
   display: block;
   font-size: 0.9rem;
   color: #5d6d7e;
   text-transform: uppercase;
   font-weight: 500;
   margin-top: 0.5rem;
 }

 .ingredients-section h2, .instructions-section h2 {
   color: #2d5a27;
   font-family: 'Playfair Display', serif;
   font-size: 1.4rem;
   margin-bottom: 1.5rem;
   font-weight: 600;
 }

 .ingredients-list {
   list-style: none;
   padding: 0;
 }

 .ingredient-item {
   display: flex;
   padding: 1rem 0;
   border-bottom: 1px solid rgba(45, 90, 39, 0.1);
   gap: 1rem;
 }

 .ingredient-measure {
   font-weight: bold;
   color: #2d5a27;
   min-width: 120px;
   flex-shrink: 0;
   font-size: 1rem;
 }

 .ingredient-name {
   color: #2c3e50;
   flex: 1;
   font-size: 1rem;
 }

 .instructions-list {
   display: flex;
   flex-direction: column;
   gap: 1.5rem;
 }

 .instruction-step {
   display: flex;
   gap: 1rem;
   align-items: flex-start;
   padding: 1rem;
   background: rgba(255, 255, 255, 0.8);
   border-radius: 15px;
 }

 .step-number {
   background: linear-gradient(135deg, #2d5a27, #4a7c59);
   color: white;
   border-radius: 50%;
   width: 45px;
   height: 45px;
   display: flex;
   align-items: center;
   justify-content: center;
   font-weight: bold;
   flex-shrink: 0;
   box-shadow: 0 4px 10px rgba(45, 90, 39, 0.3);
   font-size: 1rem;
 }

 .step-text {
   padding-top: 0.5rem;
   line-height: 1.6;
   color: #2c3e50;
   font-size: 1rem;
 }

 .no-instructions {
   text-align: center;
   color: #5d6d7e;
   font-style: italic;
   padding: 2rem;
   background: rgba(255, 255, 255, 0.5);
   border-radius: 10px;
   font-size: 1rem;
 }

 .reviews-section-detailed {
   background: white;
   border-radius: 15px;
   padding: 2rem;
   margin-bottom: 2rem;
   box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
 }

 .reviews-section-detailed h2 {
   color: #2d5a27;
   font-family: 'Playfair Display', serif;
   font-size: 1.4rem;
   margin-bottom: 1.5rem;
   font-weight: 600;
 }

 .add-review-form {
   background: linear-gradient(135deg, rgba(245, 241, 232, 0.5), rgba(255, 255, 255, 0.8));
   border: 2px solid rgba(45, 90, 39, 0.1);
   border-radius: 20px;
   padding: 2rem;
   margin-bottom: 2rem;
 }

 .rating-input {
   margin-bottom: 1.5rem;
 }

 .rating-label {
   display: block;
   font-weight: 600;
   margin-bottom: 1rem;
   color: #2c3e50;
   font-size: 1.1rem;
 }

 .star-rating-input {
   display: flex;
   gap: 0.5rem;
   justify-content: center;
 }

 .star-btn {
   font-size: 2rem;
   color: #ddd;
   cursor: pointer;
   background: none;
   border: none;
   padding: 0.5rem;
   border-radius: 50%;
   transition: all 0.3s ease;
 }

 .star-btn:hover,
 .star-btn.active {
   color: #f59e0b;
   transform: scale(1.2);
 }

 .review-textarea {
   width: 100%;
   min-height: 120px;
   border: 2px solid rgba(45, 90, 39, 0.2);
   border-radius: 15px;
   padding: 1.2rem;
   resize: vertical;
   font-family: inherit;
   margin-bottom: 1.5rem;
   font-size: 1rem;
 }

 .review-textarea:focus {
   outline: none;
   border-color: #2d5a27;
   box-shadow: 0 0 0 3px rgba(45, 90, 39, 0.1);
 }

 .review-form-actions {
   display: flex;
   gap: 1rem;
   justify-content: center;
 }

 .submit-review-btn {
   background: linear-gradient(135deg, #2d5a27, #4a7c59);
   color: white;
   border: none;
   padding: 1rem 2rem;
   border-radius: 15px;
   font-weight: 600;
   cursor: pointer;
   display: flex;
   align-items: center;
   gap: 0.8rem;
   font-size: 1rem;
   transition: all 0.3s ease;
 }

 .submit-review-btn:hover {
   background: linear-gradient(135deg, #4a7c59, #7fb069);
   transform: translateY(-2px);
   box-shadow: 0 6px 20px rgba(45, 90, 39, 0.3);
 }

 .cancel-review-btn {
   background: #6c757d;
   color: white;
   border: none;
   padding: 1rem 2rem;
   border-radius: 15px;
   cursor: pointer;
   font-weight: 500;
   transition: all 0.3s ease;
   font-size: 1rem;
 }

 .cancel-review-btn:hover {
   background: #5a6268;
   transform: translateY(-2px);
 }

 .user-reviews {
   margin-bottom: 2rem;
 }

 .user-reviews h3 {
   color: #2d5a27;
   font-size: 1.1rem;
   margin-bottom: 1rem;
   font-weight: 600;
 }

 .review-item {
   background: rgba(245, 241, 232, 0.3);
   border-radius: 10px;
   padding: 1.5rem;
   margin-bottom: 1rem;
   border-left: 4px solid #2d5a27;
 }

 .review-header {
   display: flex;
   justify-content: space-between;
   align-items: center;
   margin-bottom: 0.8rem;
 }

 .review-rating {
   color: #f59e0b;
   font-size: 1.1rem;
 }

 .review-date {
   color: #5d6d7e;
   font-size: 0.9rem;
 }

 .review-text {
   color: #2c3e50;
   line-height: 1.6;
   font-size: 1rem;
 }

 .comments-section-detailed {
   background: white;
   border-radius: 15px;
   padding: 2rem;
   box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
 }

 /* Debug info styles */
 .debug-info {
   padding: 1.5rem;
   margin: 2rem 0;
   border-radius: 15px;
   text-align: center;
   font-weight: 500;
   backdrop-filter: blur(10px);
   display: flex;
   align-items: center;
   justify-content: center;
   gap: 0.5rem;
 }
 
 .debug-info.loading {
   background: linear-gradient(135deg, rgba(33, 150, 243, 0.1), rgba(144, 202, 249, 0.1));
   color: #1976d2;
   border: 2px solid rgba(33, 150, 243, 0.3);
 }
 
 .debug-info.error {
   background: linear-gradient(135deg, rgba(244, 67, 54, 0.1), rgba(239, 154, 154, 0.1));
   color: #c62828;
   border: 2px solid rgba(244, 67, 54, 0.3);
 }
 
 .debug-info.warning {
   background: linear-gradient(135deg, rgba(255, 152, 0, 0.1), rgba(255, 204, 128, 0.1));
   color: #ef6c00;
   border: 2px solid rgba(255, 152, 0, 0.3);
 }

 .spinner {
   font-size: 1.5rem;
   animation: spin 1s linear infinite;
 }

 @keyframes spin {
   from { transform: rotate(0deg); }
   to { transform: rotate(360deg); }
 }

 /* Recipe card animation fix */
 .recipe-card {
   animation: fadeInUp 0.6s ease-out forwards;
   opacity: 0;
   transform: translateY(30px);
 }

 .recipe-card:nth-child(1) { animation-delay: 0.1s; }
 .recipe-card:nth-child(2) { animation-delay: 0.2s; }
 .recipe-card:nth-child(3) { animation-delay: 0.3s; }
 .recipe-card:nth-child(4) { animation-delay: 0.4s; }
 .recipe-card:nth-child(5) { animation-delay: 0.5s; }
 .recipe-card:nth-child(6) { animation-delay: 0.6s; }

 @keyframes fadeInUp {
   to {
     opacity: 1;
     transform: translateY(0);
   }
 }

 /* Mobile responsive fixes */
 @media (max-width: 768px) {
   .modal-content {
     width: 100%;
     height: 100vh;
     border-radius: 0;
   }

   .recipe-body {
     grid-template-columns: 1fr;
     gap: 2rem;
   }

   .recipe-header-compact {
     padding: 1rem;
   }

   .recipe-detail-title {
     font-size: 1.3rem;
   }

   .recipe-stats-bar-compact {
     flex-direction: column;
     gap: 0.5rem;
   }

   .nutrition-grid {
     grid-template-columns: repeat(4, 1fr);
   }

   .ingredients-section h2, .instructions-section h2 {
     font-size: 1.2rem;
   }

   .reviews-section-detailed h2 {
     font-size: 1.2rem;
   }
 }
</style>
