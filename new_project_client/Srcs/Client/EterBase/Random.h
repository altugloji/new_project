#ifndef __INC_ETERBASE_RANDOM_H__
#define __INC_ETERBASE_RANDOM_H__

extern void				srandom(unsigned long seed);
extern unsigned long	random();
extern float			frandom(float flLow, float flHigh);
extern long				random_range(long from, long to);

#endif
//archive's 6b9a24beef838d9382c750a6b44ccdb4
