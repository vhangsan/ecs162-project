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

  const BACKEND_BASE = import.meta.env.VITE_BACKEND_BASE || "http://localhost:8000";

  onMount(() => {
    checkAuthStatus();
    loadFilterOptions();
  });

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
        credentials: 'include'
      });
      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          user = data.user;
        }
      }
    } catch (error) {
      console.log('User not logged in');
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

      console.log('Searching for:', searchTerm);

      const params = new URLSearchParams({
        ingredients: searchTerm
      });

      if (selectedCuisine)         params.append('cuisine', selectedCuisine);
      if (selectedDiet)            params.append('diet', selectedDiet);
      if (selectedIntolerances.length > 0)
        params.append('intolerances', selectedIntolerances.join(','));
      if (selectedTime)            params.append('maxReadyTime', selectedTime);
      if (selectedMealType)        params.append('type', selectedMealType);

      params.append('number', '6');
      params.append('addRecipeInformation', 'true');

      const url = `${BACKEND_BASE}/recipes?${params.toString()}`;
      console.log('API URL:', url);

      const res = await fetch(url);
      console.log('Response status:', res.status);
      
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}: ${res.statusText}`);
      }

      const recipeResults = await res.json();
      console.log('Raw API Response:', recipeResults);
      console.log('Number of recipes received:', recipeResults?.length || 0);

      if (!Array.isArray(recipeResults)) {
        console.error('Expected array, got:', typeof recipeResults, recipeResults);
        searchError = recipeResults.error || "Invalid response format";
        recipes = [];
        loading = false;
        return;
      }

      if (recipeResults.length === 0) {
        console.log('No recipes found for these ingredients');
        searchError = "No recipes found for these ingredients. Try different ingredients or remove some filters.";
        recipes = [];
        loading = false;
        return;
      }

      recipes = recipeResults.map((r: any, index: number) => {
        console.log(`Processing recipe ${index + 1}:`, r.title, r);
        
        return {
          id: r.id,
          title: r.title || `Recipe ${r.id}`,
          image: r.image || '/Temp_Image.jpg', 
          calories: r.calories || r.nutrition?.nutrients?.find((n: any) => n.name === 'Calories')?.amount || 0,
          rating: r.spoonacularScore !== undefined
            ? Math.round(r.spoonacularScore / 20 * 10) / 10
            : 3.0,
          cuisines: r.cuisines && r.cuisines.length > 0
            ? r.cuisines
            : ["International"],
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
        };
      });
      
      console.log('Processed recipes:', recipes);
      console.log('Final recipes count:', recipes.length);
      
    } catch (error) {
      console.error("Error fetching recipes:", error);
      searchError = `Failed to fetch recipes: ${error.message}`;
      recipes = [];
    } finally {
      loading = false;
    }
  }

  function getDifficultyFromTime(minutes: number): string {
    if (minutes <= 20) return 'Easy';
    if (minutes <= 45) return 'Medium';
    return 'Hard';
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

  function submitReview() {
    if (userRating > 0 && userReview.trim()) {
      console.log('Submitting review:', { rating: userRating, review: userReview });
      showReviewForm = false;
      userRating = 0;
      userReview = "";
    }
  }

  function getNutrientValue(nutrients: any[], name: string): number {
    const nutrient = nutrients.find(n => n.name === name);
    return nutrient ? Math.round(nutrient.amount) : 0;
  }
</script>

<main class="figma-main">
  <!-- HEADER -->
  <header class="figma-header">
    <div class="header-content">
      <h1 class="website-title">WEBSITE NAME</h1>
      <div class="header-nav">
        <button class="nav-button">Home</button>
        {#if user}
          <div class="user-menu">
            <button class="nav-button" on:click={() => (showAccountSidebar = !showAccountSidebar)}>
              Account ▾
            </button>
            {#if showAccountSidebar}
              <div class="dropdown-menu">
                <div class="user-email">{user.email}</div>
                <button on:click={logout} class="logout-btn">Logout</button>
              </div>
            {/if}
          </div>
        {:else}
          <button class="nav-button" on:click={login}>Login</button>
        {/if}
      </div>
    </div>
  </header>

  <!-- HERO SECTION -->
  <section class="hero-section">
    <div class="hero-content">
    </div>
  </section>

  <!-- SEARCH SECTION -->
  <section class="search-section">
    <div class="search-tabs">
      <button class="tab-button active">USE MY INGREDIENTS</button>
      <button class="tab-button">FIND SPECIFIC RECIPE</button>
    </div>
    <div class="search-container">
      <input
        type="text"
        bind:value={ingredients}
        placeholder="Enter ingredients..."
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
        {loading ? '⏳' : '🔍'}
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
    
    {#if loading}
      <div class="debug-info loading">
        🔄 Searching for recipes...
      </div>
    {/if}
    
    {#if searchError}
      <div class="debug-info error">
        ❌ {searchError}
      </div>
    {/if}
    
    {#if recipes.length === 0 && !loading && !searchError && ingredientList.length > 0}
      <div class="debug-info warning">
        ⚠️ No recipes found. Try different ingredients or check the console for details.
      </div>
    {/if}
  </section>

  <!-- STUDENT FAVORITES -->
  <section class="favorites-section">
    <h2 class="section-title">STUDENT FAVORITES</h2>
    <div class="favorites-grid">
      <div class="recipe-card">
        <div class="recipe-image-container">
          <img src="/Temp_Image.jpg" alt="Pad Thai" class="recipe-image" />
        </div>
        <div class="recipe-info">
          <h3 class="recipe-title">PAD THAI</h3>
          <div class="rating-stars">★★★★★</div>
          <div class="recipe-meta">
            <span class="cuisine">Thai</span>
            <span class="calories">650 cal</span>
          </div>
          <div class="dietary-badge vegan">V</div>
        </div>
      </div>
      <div class="recipe-card">
        <div class="recipe-image-container">
          <img src="/Temp_Image.jpg" alt="Burger Bowl" class="recipe-image" />
        </div>
        <div class="recipe-info">
          <h3 class="recipe-title">BURGER BOWL</h3>
          <div class="rating-stars">★★★★☆</div>
          <div class="recipe-meta">
            <span class="cuisine">American</span>
            <span class="calories">598 cal</span>
          </div>
        </div>
      </div>
      <div class="recipe-card">
        <div class="recipe-image-container">
          <img src="/Temp_Image.jpg" alt="Banana Bread" class="recipe-image" />
        </div>
        <div class="recipe-info">
          <h3 class="recipe-title">BANANA BREAD</h3>
          <div class="rating-stars">★★★★★</div>
          <div class="recipe-meta">
            <span class="cuisine">Baked Good</span>
            <span class="calories">235 cal</span>
          </div>
          <div class="dietary-badge gluten-free">GF</div>
        </div>
      </div>
    </div>
  </section>

  {#if ingredientList.length > 0}
    <section class="filters-section">
      <div class="filters-container">
        <div class="ingredient-display">
          <h3>MY INGREDIENTS:</h3>
          <div class="current-ingredients">
            {#each ingredientList as ing}
              <span class="ingredient-tag">
                {ing.toUpperCase()}
                <button class="remove-tag" on:click={() => removeIngredient(ing)}>×</button>
              </span>
            {/each}
          </div>
        </div>
        <div class="meal-type-section">
          <div class="meal-type-grid">
            {#each mealTypeMapping as mealType}
              <div 
                class="meal-type-card {selectedMealType === mealType.id ? 'selected' : ''}"
                on:click={() => toggleMealType(mealType.id)}
              >
                <div class="meal-icon">{mealType.icon}</div>
                <div class="meal-label">{mealType.label}</div>
              </div>
            {/each}
          </div>
        </div>
        <!-- Filter Dropdowns -->
        <div class="filter-dropdowns">
          <!-- Time Filter -->
          <div class="filter-dropdown">
            <button class="filter-btn {selectedTime ? 'active' : ''}" on:click={() => toggleDropdown('time')}>
              TIME ▼
            </button>
            {#if activeDropdown === 'time'}
              <div class="dropdown-content">
                {#each timeOptions as option}
                  <button 
                    class="dropdown-option {selectedTime === option.value ? 'selected' : ''}"
                    on:click={() => selectFilter('time', option.value)}
                  >
                    {option.label}
                  </button>
                {/each}
              </div>
            {/if}
          </div>
          <!-- Diet Filter -->
          <div class="filter-dropdown">
            <button class="filter-btn {selectedDiet ? 'active' : ''}" on:click={() => toggleDropdown('diet')}>
              DIET ▼
            </button>
            {#if activeDropdown === 'diet'}
              <div class="dropdown-content">
                {#each availableDiets as option}
                  <button 
                    class="dropdown-option {selectedDiet === option ? 'selected' : ''}"
                    on:click={() => selectFilter('diet', option)}
                  >
                    {option}
                  </button>
                {/each}
              </div>
            {/if}
          </div>
          <!-- Intolerances Filter -->
          <div class="filter-dropdown">
            <button class="filter-btn {selectedIntolerances.length > 0 ? 'active' : ''}" on:click={() => toggleDropdown('intolerance')}>
              INTOLERANCES ▼
            </button>
            {#if activeDropdown === 'intolerance'}
              <div class="dropdown-content">
                {#each availableIntolerances as option}
                  <button 
                    class="dropdown-option {selectedIntolerances.includes(option) ? 'selected' : ''}"
                    on:click={() => toggleIntolerance(option)}
                  >
                    {option} {selectedIntolerances.includes(option) ? '✓' : ''}
                  </button>
                {/each}
              </div>
            {/if}
          </div>
          <!-- Cuisine Filter -->
          <div class="filter-dropdown">
            <button class="filter-btn {selectedCuisine ? 'active' : ''}" on:click={() => toggleDropdown('cuisine')}>
              CUISINE ▼
            </button>
            {#if activeDropdown === 'cuisine'}
              <div class="dropdown-content">
                {#each availableCuisines as option}
                  <button 
                    class="dropdown-option {selectedCuisine === option ? 'selected' : ''}"
                    on:click={() => selectFilter('cuisine', option)}
                  >
                    {option}
                  </button>
                {/each}
              </div>
            {/if}
          </div>
        </div>
        <!-- Active Filters Display -->
        {#if selectedTime || selectedDiet || selectedIntolerances.length > 0 || selectedCuisine || selectedMealType}
          <div class="active-filters">
            <span class="filter-label">Active filters:</span>
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
            <button class="clear-filters-btn" on:click={clearAllFilters}>Clear All</button>
          </div>
        {/if}
      </div>
    </section>
  {/if}

  <!-- RECIPE RESULTS -->
  {#if recipes.length > 0}
    <section class="results-section">
      <h2 class="section-title">RECIPE RESULTS ({recipes.length})</h2>
      <div class="recipes-grid">
        {#each recipes as recipe, index}
          <div class="recipe-card clickable" on:click={() => openRecipeModal(recipe)}>
            <div class="recipe-image-container">
              <img src={recipe.image} alt={recipe.title} class="recipe-image" 
                   on:error={(e) => {
                     console.log(`Image failed to load for recipe ${index}:`, recipe.image);
                     e.target.src = '/Temp_Image.jpg';
                   }}
              />
            </div>
            <div class="recipe-info">
              <h3 class="recipe-title">{recipe.title.toUpperCase()}</h3>
              <div class="rating-stars">{renderStars(recipe.rating)}</div>
              <div class="recipe-meta">
                <span class="cuisine">{recipe.cuisines[0]}</span>
                <span class="calories">{recipe.calories} cal</span>
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

  {#if showRecipeModal && selectedRecipe}
    <div class="recipe-detail-modal">
      <button class="modal-close-btn" on:click={closeRecipeModal}>×</button>
      
      <div class="recipe-header">
        <div class="recipe-content">
          <h1 class="recipe-detail-title">{selectedRecipe.title}</h1>
          
          <div class="recipe-rating-info">
            <div class="rating-display">
              <div class="rating-stars-large">{renderStars(selectedRecipe.rating)}</div>
              <span class="rating-number">{selectedRecipe.rating}</span>
              <span class="review-count">(35 Reviews)</span>
              <span class="cuisine-type">| {selectedRecipe.cuisines[0]} Cuisine</span>
            </div>
          </div>
          
          <div class="recipe-stats-bar">
            <div class="stat-item">
              <strong>Prep Time:</strong> {Math.round(selectedRecipe.readyInMinutes * 0.3)} min
            </div>
            <div class="stat-item">
              <strong>Cook Time:</strong> {Math.round(selectedRecipe.readyInMinutes * 0.7)} min
            </div>
            <div class="stat-item">
              <strong>Serving:</strong> {selectedRecipe.servings}
            </div>
          </div>
          
          <div class="recipe-actions">
            <button class="favorite-btn">
              <span class="heart-icon">♡</span>
              Favorite
            </button>
            <button class="rate-btn" on:click={() => showReviewForm = !showReviewForm}>
              <span class="star-icon">☆</span>
              Rate
            </button>
          </div>
        </div>
      </div>
      
      <div class="recipe-content">
        <div class="recipe-body">
          <div class="recipe-left">
            <img src={selectedRecipe.image} alt={selectedRecipe.title} class="recipe-detail-image" />
            
            <div class="nutrition-box">
              <h3>Nutrition Info <span class="per-serving">(per serving)</span></h3>
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
                  <p>No detailed instructions available.</p>
                {/if}
              </div>
            </div>
          </div>
        </div>
        
        <!-- Reviews Section -->
        <div class="reviews-section-detailed">
          <h2>Reviews (35)</h2>
          
          {#if showReviewForm}
            <div class="add-review-form">
              <div class="rating-input">
                <label class="rating-label">Your Rating</label>
                <div class="star-rating-input">
                  {#each [1, 2, 3, 4, 5] as star}
                    <button 
                      class="star-btn {star <= userRating ? 'active' : ''}"
                      on:click={() => setRating(star)}
                    >
                      ★
                    </button>
                  {/each}
                </div>
              </div>
              <textarea 
                bind:value={userReview}
                class="review-textarea"
                placeholder="Share your experience with this recipe..."
              ></textarea>
              <button class="submit-review-btn" on:click={submitReview}>
                Submit Review
              </button>
            </div>
          {/if}
          
          <div class="reviews-list">
            <div class="review-item">
              <div class="review-header">
                <div class="reviewer-avatar">b</div>
                <div class="reviewer-info">
                  <div class="reviewer-name">bouncybuttercup</div>
                  <div class="review-rating">★★★★☆</div>
                  <div class="review-date">05/26/25</div>
                </div>
              </div>
              <div class="review-text">so yummy! would make again</div>
            </div>
            
            <div class="review-item">
              <div class="review-header">
                <div class="reviewer-avatar">c</div>
                <div class="reviewer-info">
                  <div class="reviewer-name">crunchycherries</div>
                  <div class="review-rating">★★★☆☆</div>
                  <div class="review-date">05/18/25</div>
                </div>
              </div>
              <div class="review-text">forgot the lime...o well next time</div>
            </div>
          </div>
        </div>
        
        <!-- Comments Section -->
        <div class="comments-section-detailed">
          <Comments recipeId={selectedRecipe.id} {user} backendBase={BACKEND_BASE} />
        </div>
      </div>
    </div>
  {/if}
</main>

<style>
  .debug-info {
    padding: 1rem;
    margin: 1rem 0;
    border-radius: 8px;
    text-align: center;
    font-weight: bold;
  }
  
  .debug-info.loading {
    background: #e3f2fd;
    color: #1976d2;
    border: 1px solid #90caf9;
  }
  
  .debug-info.error {
    background: #ffebee;
    color: #c62828;
    border: 1px solid #ef9a9a;
  }
  
  .debug-info.warning {
    background: #fff3e0;
    color: #ef6c00;
    border: 1px solid #ffcc02;
  }
  
  .modal-section {
    margin-bottom: 1.5rem;
  }
  
  .star-btn.active {
    color: #ffd700;
  }
  
  .star-rating-input .star-btn:hover {
    color: #ffd700;
  }
  
  .recipe-detail-modal {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    z-index: 1000;
  }
  
  .recipe-detail-modal .recipe-content {
    position: relative;
  }
  
  .search-btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
</style>