#include "llvm/IR/PassManager.h"
#include "llvm/IR/Instructions.h"
#include "llvm/IR/Module.h"
#include "llvm/IR/Function.h"
#include "llvm/IR/IRBuilder.h"
#include "llvm/IR/InstrTypes.h"
#include "llvm/Support/raw_ostream.h" // for errs()
#include "llvm/Pass.h"

using namespace llvm;

namespace {
struct BranchTracePass : public ModulePass {
    static char ID;
    BranchTracePass() : ModulePass(ID) {}

    bool runOnModule(Module &M) override {
        LLVMContext &Context = M.getContext();
        Function *Logger = cast<Function>(
            M.getOrInsertFunction("__record_branch_hit", Type::getVoidTy(Context), Type::getInt32Ty(Context)).getCallee()
        );

        bool foundStop = false;
        int branchID = 0;

        errs() << ">>> Running BranchTracePass on module\n";

        for (Function &F : M) {
            if (F.isDeclaration()) continue;

            errs() << "Visiting function: " << F.getName() << "\n";

            for (BasicBlock &BB : F) {
                for (Instruction &I : BB) {
                    if (auto *Call = dyn_cast<CallInst>(&I)) {
                        if (Function *Callee = Call->getCalledFunction()) {
                            StringRef name = Callee->getName();
                            if (name.contains("assume_NL_stop")) {
                                foundStop = true;
                                errs() << "[*] Found assume_NL_stop at: " << *Call << "\n";
                            }
                        }
                    }

                    if (foundStop) {
                        if (auto *BI = dyn_cast<BranchInst>(&I)) {
                            if (BI->isConditional()) {
                                errs() << "[*] Found conditional branch: " << *BI << "\n";

                                for (unsigned i = 0; i < BI->getNumSuccessors(); ++i) {
                                    BasicBlock *Succ = BI->getSuccessor(i);
                                    Instruction *InsertPt = &*Succ->getFirstInsertionPt();

                                    IRBuilder<> Builder(InsertPt);
                                    Builder.CreateCall(Logger, ConstantInt::get(Type::getInt32Ty(Context), branchID));

                                    errs() << "  [+] Injected __record_branch_hit(" << branchID << ") into block: "
                                           << Succ->getName() << "\n";
                                    branchID++;
                                }
                            }
                        }
                    }
                }
            }
        }

        return true;
    }
};
}

char BranchTracePass::ID = 0;
static RegisterPass<BranchTracePass> X("branchtrace", "Trace branches after assume_nl_stop", false, false);
