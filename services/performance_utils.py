"""
Utilitaires de mesure de performance pour OCR
"""
import time
import logging
from functools import wraps
from contextlib import contextmanager
from typing import Callable, Any

logger = logging.getLogger(__name__)

def timeit_decorator(func: Callable) -> Callable:
    """
    Décorateur pour mesurer le temps d'exécution d'une fonction
    
    Usage:
        @timeit_decorator
        def ma_fonction():
            ...
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            end_time = time.perf_counter()
            duration = end_time - start_time
            logger.info(f"⏱️  {func.__name__} a pris {duration:.4f}s")
            print(f"⏱️  {func.__name__} a pris {duration:.4f}s")
    return wrapper


@contextmanager
def timer(description: str = "Opération"):
    """
    Gestionnaire de contexte pour mesurer des blocs de code
    
    Usage:
        with timer("Prétraitement image"):
            preprocess_for_ocr(image)
    """
    start_time = time.perf_counter()
    try:
        yield
    finally:
        end_time = time.perf_counter()
        duration = end_time - start_time
        logger.info(f"⏱️  {description} a pris {duration:.4f}s")
        print(f"⏱️  {description} a pris {duration:.4f}s")


class PerformanceTracker:
    """
    Classe pour tracker les performances d'un pipeline complet
    """
    def __init__(self, name: str = "Pipeline"):
        self.name = name
        self.steps = {}
        self.start_time = None
        self.total_time = None
    
    def start(self):
        """Démarre le tracking"""
        self.start_time = time.perf_counter()
        self.steps = {}
        print(f"\n{'='*60}")
        print(f"🚀 Début du tracking: {self.name}")
        print(f"{'='*60}")
    
    def step(self, step_name: str):
        """Marque le début d'une étape"""
        if self.start_time is None:
            self.start()
        return self._StepContext(self, step_name)
    
    def stop(self):
        """Arrête le tracking et affiche le rapport"""
        if self.start_time is None:
            return
        
        self.total_time = time.perf_counter() - self.start_time
        self._print_report()
    
    def _print_report(self):
        """Affiche un rapport détaillé des performances"""
        print(f"\n{'='*60}")
        print(f"📊 RAPPORT DE PERFORMANCE: {self.name}")
        print(f"{'='*60}")
        
        if not self.steps:
            print("Aucune étape enregistrée")
            return
        
        # Trier par temps décroissant
        sorted_steps = sorted(self.steps.items(), key=lambda x: x[1], reverse=True)
        
        print(f"\n{'Étape':<40} {'Temps':<12} {'%':<8}")
        print(f"{'-'*60}")
        
        for step_name, duration in sorted_steps:
            percentage = (duration / self.total_time * 100) if self.total_time > 0 else 0
            print(f"{step_name:<40} {duration:>8.4f}s   {percentage:>5.1f}%")
        
        print(f"{'-'*60}")
        print(f"{'TEMPS TOTAL':<40} {self.total_time:>8.4f}s   100.0%")
        print(f"{'='*60}\n")
    
    class _StepContext:
        """Gestionnaire de contexte pour une étape"""
        def __init__(self, tracker, step_name):
            self.tracker = tracker
            self.step_name = step_name
            self.step_start = None
        
        def __enter__(self):
            self.step_start = time.perf_counter()
            print(f"  ▶️  {self.step_name}...")
            return self
        
        def __exit__(self, *args):
            duration = time.perf_counter() - self.step_start
            self.tracker.steps[self.step_name] = duration
            print(f"  ✅ {self.step_name} terminé en {duration:.4f}s")


def compare_performance(func: Callable, *test_cases, iterations: int = 1) -> None:
    """
    Compare les performances d'une fonction sur plusieurs cas de test
    
    Args:
        func: Fonction à tester
        test_cases: Tuples (description, *args, **kwargs)
        iterations: Nombre d'itérations par cas
    """
    print(f"\n{'='*60}")
    print(f"📈 COMPARAISON DE PERFORMANCE: {func.__name__}")
    print(f"{'='*60}\n")
    
    results = []
    
    for test_case in test_cases:
        description = test_case[0]
        args = test_case[1] if len(test_case) > 1 else ()
        kwargs = test_case[2] if len(test_case) > 2 else {}
        
        times = []
        for i in range(iterations):
            start = time.perf_counter()
            try:
                func(*args, **kwargs)
            except Exception as e:
                print(f"❌ Erreur dans {description}: {e}")
                break
            times.append(time.perf_counter() - start)
        
        if times:
            avg_time = sum(times) / len(times)
            min_time = min(times)
            max_time = max(times)
            results.append((description, avg_time, min_time, max_time))
    
    # Afficher les résultats
    print(f"{'Cas de test':<40} {'Moy.':<12} {'Min.':<12} {'Max.':<12}")
    print(f"{'-'*60}")
    for desc, avg, min_t, max_t in results:
        print(f"{desc:<40} {avg:>8.4f}s   {min_t:>8.4f}s   {max_t:>8.4f}s")
    print(f"{'='*60}\n")