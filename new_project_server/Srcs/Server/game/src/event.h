#ifndef __INC_LIBTHECORE_EVENT_H__
#define __INC_LIBTHECORE_EVENT_H__

#include <cstddef>

/**
 * Base class for all event info data
 */
struct event_info_data
{
	event_info_data() {}
	virtual ~event_info_data() {}
};

typedef struct event EVENT;

template<class T>
class intrusive_ptr {
public:
	intrusive_ptr() : px(nullptr) {}
	intrusive_ptr(T* p, bool add_ref = true) : px(p) { if (px && add_ref) intrusive_ptr_add_ref(px); }
	intrusive_ptr(const intrusive_ptr& rhs) : px(rhs.px) { if (px) intrusive_ptr_add_ref(px); }
	intrusive_ptr(intrusive_ptr&& rhs) noexcept : px(rhs.px) { rhs.px = nullptr; }
	~intrusive_ptr() { if (px) intrusive_ptr_release(px); }
	intrusive_ptr& operator=(const intrusive_ptr& rhs) { intrusive_ptr(rhs).swap(*this); return *this; }
	intrusive_ptr& operator=(intrusive_ptr&& rhs) noexcept { intrusive_ptr(static_cast<intrusive_ptr&&>(rhs)).swap(*this); return *this; }
	intrusive_ptr& operator=(T* rhs) { intrusive_ptr(rhs).swap(*this); return *this; }
	void reset() { intrusive_ptr().swap(*this); }
	void reset(T* rhs) { intrusive_ptr(rhs).swap(*this); }
	T* get() const { return px; }
	T& operator*() const { return *px; }
	T* operator->() const { return px; }
	explicit operator bool() const { return px != nullptr; }
	bool operator!() const { return px == nullptr; }
	void swap(intrusive_ptr& rhs) { T* tmp = px; px = rhs.px; rhs.px = tmp; }
	friend bool operator==(const intrusive_ptr& a, const intrusive_ptr& b) { return a.px == b.px; }
	friend bool operator!=(const intrusive_ptr& a, const intrusive_ptr& b) { return a.px != b.px; }
	friend bool operator==(const intrusive_ptr& a, std::nullptr_t) { return a.px == nullptr; }
	friend bool operator==(std::nullptr_t, const intrusive_ptr& a) { return a.px == nullptr; }
	friend bool operator!=(const intrusive_ptr& a, std::nullptr_t) { return a.px != nullptr; }
	friend bool operator!=(std::nullptr_t, const intrusive_ptr& a) { return a.px != nullptr; }
private:
	T* px;
};

template<class T>
T* get_pointer(const intrusive_ptr<T>& p) { return p.get(); }

typedef intrusive_ptr<EVENT> LPEVENT;
typedef long (*TEVENTFUNC) (LPEVENT event, long processing_time);

#define EVENTFUNC(name)	long (name) (LPEVENT event, long processing_time)
#define EVENTINFO(name) struct name : public event_info_data

struct TQueueElement;

struct event
{
	event() : func(nullptr), info(nullptr), q_el(nullptr), ref_count(0) {}
	~event() {
		if (info != nullptr) {
			M2_DELETE(info);
		}
	}
	TEVENTFUNC			func;
	event_info_data* 	info;
	TQueueElement *		q_el;
	char				is_force_to_end;
	char				is_processing;

	size_t ref_count;
};

extern void intrusive_ptr_add_ref(EVENT* p);
extern void intrusive_ptr_release(EVENT* p);

template<class T> // T should be a subclass of event_info_data
T* AllocEventInfo() {
	return M2_NEW T;
}

extern void		event_destroy();
extern int		event_process(int pulse);
extern int		event_count();

#define event_create(func, info, when) event_create_ex(func, info, when)
extern LPEVENT	event_create_ex(TEVENTFUNC func, event_info_data* info, long when);
extern void		event_cancel(LPEVENT * event);
extern long		event_processing_time(LPEVENT event);
extern long		event_time(LPEVENT event);
extern void		event_reset_time(LPEVENT event, long when);
extern void		event_set_verbose(int level);

extern event_info_data* FindEventInfo(DWORD dwID);
extern event_info_data*	event_info(LPEVENT event);

#define EVENT_CANCEL_EX(event) if (event) { event_cancel(&event); event = nullptr; }
#endif
//archive's 6b9a24beef838d9382c750a6b44ccdb4
