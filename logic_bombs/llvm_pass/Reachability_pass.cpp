#include "llvm/IR/PassManager.h"
#include "llvm/IR/Instructions.h"
#include "llvm/IR/Module.h"
#include "llvm/IR/Function.h"
#include "llvm/IR/IRBuilder.h"
#include "llvm/IR/InstrTypes.h"
#include "llvm/Support/raw_ostream.h"
#include "llvm/Pass.h"

using namespace llvm;

namespace {
struct RecordReachStartPass : public ModulePass {
    static char ID;
    RecordReachStartPass() : ModulePass(ID) {}

    bool runOnModule(Module &M) override {
        LLVMContext &Context = M.getContext();

        // Get or insert the __record_reach_start function (void function with no args)
        FunctionCallee Logger = M.getOrInsertFunction("__record_reach_start", Type::getVoidTy(Context));

        bool injected = false;

        for (Function &F : M) {
            if (F.isDeclaration()) continue;

            for (BasicBlock &BB : F) {
                for (auto BI = BB.begin(); BI != BB.end(); ++BI) {
                    if (auto *Call = dyn_cast<CallInst>(&*BI)) {
                        if (Function *Callee = Call->getCalledFunction()) {
                            if (Callee->getName().contains("assume_NL_start")) {
                                errs() << "[*] Found assume_NL_start at: " << *Call << "\n";

                                IRBuilder<> Builder(Call);
                                Builder.CreateCall(Logger);

                                errs() << "[+] Injected __record_reach_start() before assume_NL_start\n";
                                injected = true;
                                break; // Inject only once
                            }
                        }
                    }
                }

                if (injected) break;
            }

            if (injected) break;
        }

        return injected;
    }
};
}

char RecordReachStartPass::ID = 0;
static RegisterPass<RecordReachStartPass> X("inject-reach-marker", "Inject __record_reach_start before assume_NL_start", false, false);
