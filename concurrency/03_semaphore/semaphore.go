package semaphore

import (
	"primitives/internal/futex"
	"sync/atomic"
)

type Semaphore struct {
	permits uint32
	waiters int32 // Awake зовется только когда есть кого будить
}

func New(n int) *Semaphore {
	if n < 0 {
		panic("semaphore: отрицательное число разрешений")
	}
	return &Semaphore{permits: uint32(n)}
}

func (s *Semaphore) Acquire() {
	for {
		permits := atomic.LoadUint32(&s.permits)
		if permits > 0 {
			// Если перехватят начнем сначала
			if atomic.CompareAndSwapUint32(&s.permits, permits, permits-1) {
				return
			}
			continue
		}
		atomic.AddInt32(&s.waiters, 1)
		// встали в очередь и перепроверяем: разрешение могли вернуть, пока
		// мы не были в счётчике ждущих, тогда Release нас не разбудит
		if atomic.LoadUint32(&s.permits) != 0 {
			atomic.AddInt32(&s.waiters, -1)
			continue
		}
		// Спим на нуле; Wait атомарно проверяет значение, так что между
		// проверкой и засыпанием Wake нас не потеряет
		futex.Wait(&s.permits, 0)
		atomic.AddInt32(&s.waiters, -1)
	}
}

func (s *Semaphore) TryAcquire() bool {
	for {
		permits := atomic.LoadUint32(&s.permits)
		if permits == 0 {
			return false
		}
		if atomic.CompareAndSwapUint32(&s.permits, permits, permits-1) {
			return true
		}
	}
}

func (s *Semaphore) Release() {
	atomic.AddUint32(&s.permits, 1)
	// будим одного только если кто-то ждет, иначе поход в ядро впустую
	if atomic.LoadInt32(&s.waiters) != 0 {
		futex.Wake(&s.permits)
	}
}

func (s *Semaphore) Available() int {
	return int(atomic.LoadUint32(&s.permits))
}
