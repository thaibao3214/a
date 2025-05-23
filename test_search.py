from image_search import ImageSearchEngine
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

def test_search():
    # Initialize search engine
    print("Initializing search engine...")
    engine = ImageSearchEngine()
    
    # If features database doesn't exist, build it
    if not Path('data/features/image_features.pkl').exists():
        print("Building features database...")
        engine.build_features_database()
    
    # Select a test image from test set
    test_image = Path('data/processed/test/ga/256.jpeg')
    if not test_image.exists():
        print("Please provide a valid test image path")
        return
    
    # Search for similar images
    print(f"\nSearching similar images for: {test_image.name}")
    results = engine.search(test_image, top_k=5)
    
    # Display results
    print("\nSearch Results:")
    for i, result in enumerate(results, 1):
        print(f"\n{i}. Class: {result['class']}")
        print(f"   Path: {result['path']}")
        print(f"   Similarity Score: {result['similarity']:.4f}")
    
    # Visualize results
    plt.figure(figsize=(15, 3))
    
    # Show query image
    plt.subplot(1, 6, 1)
    plt.imshow(mpimg.imread(test_image))
    plt.title('Query Image')
    plt.axis('off')
    
    # Show similar images
    for i, result in enumerate(results, 2):
        plt.subplot(1, 6, i)
        plt.imshow(mpimg.imread(result['path']))
        plt.title(f'Score: {result["similarity"]:.2f}')
        plt.axis('off')
    
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    test_search()