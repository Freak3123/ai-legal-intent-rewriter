import { NextResponse } from 'next/server';
import bcrypt from 'bcryptjs';
import { connectDb } from '@/lib/db/mongoose';
import { User } from '@/lib/db/models/User';
import { signupSchema } from '@/lib/validations';

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const parsed = signupSchema.safeParse(body);
    if (!parsed.success) {
      return NextResponse.json(
        { error: { code: 'INVALID_INPUT', message: 'Invalid signup data', details: parsed.error.flatten() } },
        { status: 400 }
      );
    }

    await connectDb();

    const existing = await User.findOne({ email: parsed.data.email.toLowerCase() }).lean();
    if (existing) {
      return NextResponse.json(
        { error: { code: 'EMAIL_TAKEN', message: 'An account with that email already exists' } },
        { status: 409 }
      );
    }

    const passwordHash = await bcrypt.hash(parsed.data.password, 12);
    const user = await User.create({
      email: parsed.data.email.toLowerCase(),
      name: parsed.data.name,
      passwordHash,
      provider: 'credentials',
    });

    return NextResponse.json(
      { id: user._id.toString(), email: user.email, name: user.name },
      { status: 201 }
    );
  } catch (err) {
    console.error('[signup] error:', err);
    return NextResponse.json(
      { error: { code: 'INTERNAL_ERROR', message: 'Could not create account' } },
      { status: 500 }
    );
  }
}
